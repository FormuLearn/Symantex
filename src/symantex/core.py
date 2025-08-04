from __future__ import annotations
"""Symantex — LaTeX ➜ SymPy via LLMs.

v0.2 — adds a prompt rule that **flattens subscripts / superscripts**.
  • All LaTeX identifiers like R_{r}^{val} ⇒ Symbol("R_r_val")
  • Disallows interpretations such as R(r)**v or nested Symbol(Symbol(...)).
Nothing else in the public API changed.
"""

import json
import os
import re
from typing import List, Optional, Tuple, Union

import aiohttp
import backoff
import asyncio
from tqdm.asyncio import tqdm_asyncio


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

    _JSON_MODELS = {
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4o-2024-11-20",
        "o3",
        "o3-mini",
        "o4-mini",
        "o1",
        "o1-pro",
        "gpt-4.1",
        "gpt-4.1-nano",
        "gpt-4.1-mini",
    }
    _JSON_PROVIDERS = {"openai"}

    # ---------------------------------------------------------------------#
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini") -> None:
        self.set_provider(provider)
        self.set_model(model)
        self._api_key: Optional[str] = None
        self._custom_locals: dict[str, sympy.Basic] = {}

    # ---------------------------------------------------------------------#
    # API‑key helper
    def register_key(self, api_key: str) -> None:
        self._api_key = api_key
        if self.provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key

    # ---------------------------------------------------------------------#
    # Convenience: persistent custom locals for the instance
    def register_locals(self, mapping: dict[str, sympy.Basic]) -> None:
        if not isinstance(mapping, dict):
            raise TypeError("register_locals() expects a dict-like object")
        self._custom_locals = dict(mapping)          # defensive copy

    def clear_locals(self) -> None:
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
    @llm.call(provider="openai", model="gpt-4o-mini", json_mode=True)
    async def _mirascope_call_async(self, prompt: str) -> str:  # pragma: no cover
        return prompt

    # ---------------------------------------------------------------------#
    # Public API
    async def to_sympy_async(
        self,
        latex: str,
        context: Optional[str] = None,
        *,
        extra_locals: Optional[dict[str, sympy.Basic]] = None,
        output_notes: bool = False,
        failure_logs: bool = False,
        max_retries: int = 2,
        per_call_timeout: float = 30.0,
    ) -> Union[List[sympy.Expr], Tuple[List[sympy.Expr], str, bool]]:
        if not self._api_key:
            raise APIKeyMissingError("Call register_key() first.")

        prompt = self._build_prompt(latex, context)

        for attempt in range(max_retries + 1):
            try:
                raw_json = await asyncio.wait_for(
                    self._run_llm_async(prompt, failure_logs), timeout=per_call_timeout
                )
            except Exception as e:
                if attempt == max_retries:
                    raise
                prompt = self._repair_prompt(prompt, e)
                continue

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
                prompt = self._repair_prompt(prompt, err)

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
        if not self._api_key:
            raise APIKeyMissingError("Call register_key() first.")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # no running loop, safe to block
            return asyncio.run(
                self.to_sympy_async(
                    latex,
                    context,
                    extra_locals=extra_locals,
                    output_notes=output_notes,
                    failure_logs=failure_logs,
                    max_retries=max_retries,
                )
            )
        else:
            # already in an event loop: require async usage
            raise RuntimeError(
                "Event loop already running; call to_sympy_async instead of to_sympy."
            )
        
        
    # ---------------------------------------------------------------------#
    # Prompt construction
    def _build_prompt(self, latex: str, context: Optional[str]) -> str:
        GOLD_EXAMPLE = r"""
LaTeX: R_{r}^{\mathrm{val}} = \frac 1 k \sum_{j=1}^k R_{rj}^{\mathrm{val}}
JSON:
{
  "exprs": ["Eq(R_r_val, Sum(R_rj_val, (j, 1, k))/k)"],
  "notes": "validation reward averaged over k folds",
  "multiple": false
}
""".strip()

        parts = [
            "You are Symantex — convert LaTeX to **valid SymPy strings**.",
            "",
            "Return exactly **one** JSON object (no markdown fences).",
            "",
            GOLD_EXAMPLE,
            "",
            "### REQUIREMENTS",
            "1. Each string in \"exprs\" must parse with `sympy.parse_expr`.",
            "2. Use Eq(lhs, rhs) — never a bare '='.",
            "3. Sums/Integrals → Sum(...), Integral(...) — no comprehensions.",
            "4. Bare identifiers (N, Theta, …) stay bare; do *not* quote them.",
            "5. Reserved names N, E, I, pi are symbols unless *called*.",
            "6. For a parameterised operator (\\mathcal{N}_θ(u)) write N_theta(u),",
            "   **never** N(theta)(u).",
            "7. Unknown ops (argmin, relu, …) → plain calls (argmin(...)).",
            "8. Field \"multiple\" is true iff len(exprs) > 1.",
            "9. Think step-by-step internally; show only the final JSON.",
            "10. **Flatten every sub-/superscript into the symbol name**:",
            "    • X_{i}      →  X_i",
            "    • W^{out}    →  W_out",
            "    • R_{r}^{val}→  R_r_val",
            "    Do NOT output function calls like R(r) or exponentiation like R**val.",
            "",
            f"Context: {context}" if context else "",
            f"LATEX INPUT: {latex}",
        ]
        return "\n".join(filter(None, parts))

    # ---------------------------------------------------------------------#
    # LLM call + envelope handling
    async def _run_llm_async(self, prompt: str, failure_logs: bool) -> str:
        if not self._api_key:
            raise APIKeyMissingError("Call register_key() first.")

        call = llm.override(self._mirascope_call_async, provider=self.provider, model=self.model)
        reply = await call(prompt)
        raw = reply.content if hasattr(reply, "content") else reply

        try:
            maybe = json.loads(raw)
            if isinstance(maybe, dict) and "error" in maybe:
                msg = maybe["error"].get("message", "unknown")
                raise StructuredOutputError(f"OpenAI validation error: {msg}")
        except json.JSONDecodeError:
            pass

        return raw
    # ---------------------------------------------------------------------#
    # JSON + SymPy validation
    def _parse_and_validate(
        self,
        raw_json: str,
        extra_locals: dict[str, sympy.Basic],
    ) -> Tuple[List[sympy.Expr], str, bool]:
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
            locals_map = {**_BASE_LOCALS, **self._custom_locals}
            if extra_locals:
                locals_map.update(extra_locals)

            # Promote identifiers followed by “(” to Function — even for N/E/I/pi
            for fname in _FUNC_CALL_RE.findall(code):
                locals_map[fname] = sympy.Function(fname)

            try:
                parsed.append(
                    parse_expr(code, transformations=_TRANSFORMATIONS, local_dict=locals_map)
                )
                continue
            except Exception:
                fixed = _flatten_nested_call(code)
                if fixed:
                    try:
                        parsed.append(
                            parse_expr(fixed, transformations=_TRANSFORMATIONS, local_dict=locals_map)
                        )
                        continue
                    except Exception:
                        pass
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
