from __future__ import annotations

"""Symantex — LaTeX ➜ SymPy via LLMs.

This version (0.1) introduces **custom locals** support.  Pass a mapping
of name → SymPy object at call time (`extra_locals=`) or register it once
per instance with the convenience helper `register_locals()`.  Nothing
else in the public API changed. """

import json
import os
import re
from typing import List, Optional, Tuple, Union

import sympy
from mirascope import llm
from sympy.parsing.sympy_parser import (
    convert_equals_signs,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from symantex.errors import (
    APIKeyMissingError,
    EmptyExpressionsError,
    StructuredOutputError,
    SympyConversionError,
    UnsupportedModelError,
    UnsupportedProviderError,
)

# ---------------------------------------------------------------------------#
_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_equals_signs,
)

# ---------------------------------------------------------------------------#
# Names that SymPy ships as *functions* or constants but we usually need
# as plain variables; we’ll upgrade them back to Function if the LLM
# explicitly calls them with “name( … )”.
_AMBIG = {"N", "E", "I", "pi"}

_BASE_LOCALS = {
    "Eq": sympy.Eq,
    "Sum": sympy.Sum,
    "Integral": sympy.Integral,
    "symbols": sympy.symbols,
    "IndexedBase": sympy.IndexedBase,
    # default to Symbol for the ambiguous ones
    **{name: sympy.Symbol(name) for name in _AMBIG},
}

# regex to find identifiers immediately followed by “(”
_FUNC_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_NESTED_CALL_RE = re.compile(
    r"\b([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)\s*\(\s*([^\)]+?)\s*\)"
)


def _flatten_nested_call(code: str) -> str | None:
    """Convert f(a)(b)  ->  f_a(b)
    Only fires when both a and the outer function are single identifiers.
    Returns the modified string, or None if no change.
    """
    new = _NESTED_CALL_RE.sub(r"\1_\2(\3)", code)
    return new if new != code else None


# ---------------------------------------------------------------------------#
class Symantex:
    """Convert LaTeX ➜ SymPy, delegating JSON formatting to an LLM."""

    _JSON_MODELS = {"gpt-4o-mini"}
    _JSON_PROVIDERS = {"openai"}

    # ---------------------------------------------------------------------#
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini") -> None:
        self.set_provider(provider)
        self.set_model(model)
        self._api_key: Optional[str] = None
        self._custom_locals: dict[str, sympy.Basic] = {}

    # ---------------------------------------------------------------------#
    # API-key helper
    def register_key(self, api_key: str) -> None:
        self._api_key = api_key
        if self.provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key

    # ---------------------------------------------------------------------#
    # Convenience: persistent custom locals for the instance
    def register_locals(self, mapping: dict[str, sympy.Basic]) -> None:
        """Store ``mapping`` as an overlay applied to every call.

        This is sugar for interactive sessions; heavy‑duty codebases may
        prefer the stateless ``extra_locals`` kwarg on :py:meth:`to_sympy`.
        """
        if not isinstance(mapping, dict):
            raise TypeError("register_locals() expects a dict-like object")
        # Copy to avoid surprises if caller mutates later
        self._custom_locals = dict(mapping)

    def clear_locals(self) -> None:
        """Remove any registered locals overlay."""
        self._custom_locals.clear()

    # ---------------------------------------------------------------------#
    # Config setters with validation
    def set_model(self, model: str) -> None:
        if model not in self._JSON_MODELS:
            raise UnsupportedModelError(f"Model '{model}' cannot run in JSON mode.")
        self.model = model

    def set_provider(self, provider: str) -> None:
        if provider not in self._JSON_PROVIDERS:
            raise UnsupportedProviderError(f"Provider '{provider}' is unknown.")
        self.provider = provider

    # ---------------------------------------------------------------------#
    # LLM wrapper (Mirascope handles JSON mode)
    @llm.call(provider="openai", model="gpt-4o-mini", json_mode=True)
    def _mirascope_call(self, prompt: str) -> str:  # pragma: no cover
        return prompt

    # ---------------------------------------------------------------------#
    # Public API
    def to_sympy(
        self,
        latex: str,
        context: Optional[str] = None,
        *,
        extra_locals: Optional[dict[str, sympy.Basic]] = None,
        output_notes: bool = False,
        failure_logs: bool = False,
        max_retries: int = 2,
    ) -> Union[List[sympy.Expr], Tuple[List[sympy.Expr], str, bool]]:
        """Convert *latex* into SymPy expressions.

        Parameters
        ----------
        latex
            The LaTeX string to convert.
        context
            Optional natural‑language context sent to the LLM.
        extra_locals
            Mapping of *name → SymPy object* merged with the internal base
            dictionary when parsing.  Shadows both built‑in and
            previously‑registered names.
        """
        if not self._api_key:
            raise APIKeyMissingError("Call register_key() first.")

        prompt = self._build_prompt(latex, context)

        for attempt in range(max_retries + 1):
            raw_json = self._run_llm(prompt, failure_logs)

            try:
                parsed, notes, multiple = self._parse_and_validate(
                    raw_json, extra_locals or {}
                )
                return (parsed, notes, multiple) if output_notes else (parsed, multiple)

            except (StructuredOutputError, SympyConversionError) as err:
                if attempt == max_retries:
                    if failure_logs and isinstance(err, SympyConversionError):
                        err.notes = f"Prompt:\n{prompt}\n\nLLM output:\n{raw_json}"
                    raise
                prompt = self._repair_prompt(prompt, err)  # Reflexion loop

    # ---------------------------------------------------------------------#
    # Prompt construction
    def _build_prompt(self, latex: str, context: Optional[str]) -> str:
        GOLD_EXAMPLE = r"""
LaTeX: \alpha = \arg\min_{x\in\mathbb{R}} \frac 1 N \sum_{i=1}^N f(x_i)
JSON:
{
  "exprs": ["Eq(alpha, argmin(x, Symbol('R'), Sum(f(x_i), (i, 1, N))/N))"],
  "notes": "empirical risk minimisation over ℝ",
  "multiple": false
}
""".strip()

        parts = [
            "You are Symantex — convert LaTeX to **valid SymPy strings**.",
            "",
            "Return exactly **one** JSON object (no markdown fences).",
            "",
            GOLD_EXAMPLE,
            "",
            "### REQUIREMENTS",
            "1. Each string in \"exprs\" must parse with `sympy.parse_expr`.",
            "2. Use Eq(lhs, rhs) — never a bare '='.",
            "3. Sums/Integrals → Sum(...), Integral(...) — no comprehensions.",
            "4. Bare symbols like N, Theta (or symbols('Theta')); do not quote them.",
            "5. Reserved names N, E, I, pi are symbols unless *called*.",
            "6. To denote a *parameterised* operator (\\mathcal{N}_θ(u))",
            "write **N_theta(u)** — NEVER N(theta)(u).",
            "7. Unknown ops (argmin, relu, …) → plain calls (argmin(...)).",
            "8. Field \"multiple\" is true iff len(exprs) > 1.",
            "9. Think step-by-step internally; show only the final JSON.",
            "",
            f"Context: {context}" if context else "",
            f"LATEX INPUT: {latex}",
        ]
        return "\n".join(filter(None, parts))

    # ---------------------------------------------------------------------#
    # LLM call + envelope handling
    def _run_llm(self, prompt: str, failure_logs: bool) -> str:
        call = llm.override(self._mirascope_call, provider=self.provider, model=self.model)
        reply = call(prompt)
        raw = reply.content if hasattr(reply, "content") else reply

        # If OpenAI JSON-mode blocked the content, let Reflexion handle it
        try:
            maybe = json.loads(raw)
            if isinstance(maybe, dict) and "error" in maybe:
                msg = maybe["error"].get("message", "unknown")
                raise StructuredOutputError(f"OpenAI validation error: {msg}")
        except json.JSONDecodeError:
            pass

        return raw

    # ---------------------------------------------------------------------#
    # JSON + SymPy validation
    def _parse_and_validate(
        self,
        raw_json: str,
        extra_locals: dict[str, sympy.Basic],
    ) -> Tuple[List[sympy.Expr], str, bool]:
        """Parse JSON from the LLM and validate SymPy expressions."""
        try:
            data = json.loads(raw_json)
        except Exception as e:
            raise StructuredOutputError(f"Invalid JSON: {e}") from e

        if not all(k in data for k in ("exprs", "notes", "multiple")):
            raise StructuredOutputError(
                f"Missing keys in JSON. Got: {list(data.keys())}"
            )

        expr_strs = data["exprs"]
        if isinstance(expr_strs, str):
            expr_strs, data["multiple"] = [expr_strs], False
        if not isinstance(expr_strs, list):
            raise StructuredOutputError('"exprs" must be a list of strings')
        if not expr_strs:
            raise EmptyExpressionsError("No expressions returned by the model.")

        parsed, failures = [], []
        for code in expr_strs:
            # fresh copy per expression
            locals_map: dict[str, sympy.Basic] = {**_BASE_LOCALS, **self._custom_locals}
            if extra_locals:
                locals_map.update(extra_locals)

            # Promote identifiers followed by “(” to Function — even for N/E/I/pi
            for fname in _FUNC_CALL_RE.findall(code):
                locals_map[fname] = sympy.Function(fname)

            try:
                parsed.append(
                    parse_expr(
                        code, transformations=_TRANSFORMATIONS, local_dict=locals_map
                    )
                )
                continue
            except Exception:
                # one-shot heuristic: f(a)(b)  ->  f_a(b)
                fixed = _flatten_nested_call(code)
                if fixed:
                    try:
                        parsed.append(
                            parse_expr(
                                fixed,
                                transformations=_TRANSFORMATIONS,
                                local_dict=locals_map,
                            )
                        )
                        continue
                    except Exception:
                        pass  # fall through
                failures.append(code)

        if failures:
            raise SympyConversionError("Parse error", "; ".join(failures))

        multiple = bool(data["multiple"]) if len(expr_strs) > 1 else False
        return parsed, data["notes"], multiple

    # ---------------------------------------------------------------------#
    # Reflexion repair prompt
    @staticmethod
    def _repair_prompt(prev_prompt: str, err: Exception) -> str:
        return (
            "Your last JSON was rejected.\n"
            f"Reason: {err}\n\n"
            "Reread the rules, THINK, then output **one line** containing only a "
            "corrected JSON object with keys `exprs`, `notes`, `multiple`."
        )
