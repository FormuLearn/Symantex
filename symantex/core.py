# symantex/core.py

import os
import json
from typing import List, Optional, Union

from mirascope import llm
from symantex.errors import (
    APIKeyMissingError,
    UnsupportedModelError,
    StructuredOutputError,
    EmptyExpressionsError,
    SympyConversionError
)
import sympy
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_equals_signs
)


# Enable implicit multiplication, convert "a=b" → Eq(a,b), etc.
_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_equals_signs,
)


class Symantex:
    """
    Convert LaTeX input into Sympy expressions by leveraging Mirascope's JSON Mode.
    """

    _JSON_MODELS = {"gpt-4o-mini"}

    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini") -> None:
        if model not in self._JSON_MODELS:
            raise UnsupportedModelError(f"Model '{model}' does not support JSON Mode.")
        self.provider = provider
        self.model = model
        self._api_key: Optional[str] = None

    def register_key(self, api_key: str) -> None:
        self._api_key = api_key
        if self.provider.lower() == "openai":
            os.environ["OPENAI_API_KEY"] = api_key

    @llm.call(provider="openai", model="gpt-4o-mini", json_mode=True)
    def _mirascope_call(self, prompt: str) -> str:
        return prompt

    def to_sympy(
        self,
        latex: str,
        context: Optional[str] = None,
        output_notes: bool = False
    ) -> Union[List[sympy.Expr], tuple[List[sympy.Expr], str]]:
        if not self._api_key:
            raise APIKeyMissingError("API key missing; call register_key() first.")

        # Build a guiding prompt
        prompt_lines = [
            "Return a JSON object with exactly two keys:",
            '  "exprs": a list of Sympy-parsable strings,',
            '  "notes": a string of assumptions/comments.',
            "",
            "Use only valid Python/Sympy code:",
            "- Eq(lhs, rhs) for equations (no `=`).",
            "- Sum(w_j*u_j, (j,1,K)) for sums (no comprehensions).",
            "- symbols('u1:K+1') or IndexedBase('u') for sequences, no `...`.",
            "",
            f"Latex: {latex}"
        ]
        if context:
            prompt_lines.insert(-1, f"Context: {context}")
        prompt = "\n".join(prompt_lines)

        call_fn = llm.override(self._mirascope_call,
                               provider=self.provider,
                               model=self.model)
        try:
            response = call_fn(prompt)
            raw = getattr(response, "content", response)
        except Exception as e:
            raise StructuredOutputError(str(e)) from e

        # Parse the JSON
        try:
            data = json.loads(raw)
        except Exception as e:
            raise StructuredOutputError(f"Invalid JSON: {e}") from e

        if not isinstance(data, dict) or "exprs" not in data or "notes" not in data:
            raise StructuredOutputError(f"Expected keys 'exprs' and 'notes', got: {data}")

        expr_strs = data["exprs"]
        notes = data["notes"]

        if not isinstance(expr_strs, list):
            raise StructuredOutputError(f"'exprs' is not a list: {expr_strs}")
        if len(expr_strs) == 0:
            raise EmptyExpressionsError("No expressions returned by model.")

        # Try to parse each string, collect successes & failures
        parsed: List[sympy.Expr] = []
        failures: List[str] = []
        for s in expr_strs:
            try:
                parsed.append(parse_expr(s, transformations=_TRANSFORMATIONS))
            except Exception:
                failures.append(s)

        if not parsed:
            # none succeeded → error
            combined = "; ".join(failures)
            raise SympyConversionError(
                f"All returned exprs failed to parse",
                combined
            )

        # If some failed but at least one worked, drop the bad ones
        if failures and output_notes:
            # append a warning to the model notes
            notes = (
                notes.strip()
                + "\n\n"
                + "Note: dropped unparseable expressions:\n  - "
                + "\n  - ".join(failures)
            )

        return (parsed, notes) if output_notes else parsed
