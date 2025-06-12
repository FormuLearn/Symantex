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


class Symantex:
    """
    Convert LaTeX input into Sympy expressions by leveraging Mirascope's JSON Mode.
    """

    # Known models that support JSON Mode
    _JSON_MODELS = {
        "gpt-4o-mini",
    }

    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini") -> None:
        """
        :param provider: The LLM provider to use (e.g., "openai").
        :param model: The model name; must support JSON Mode.
        :raises UnsupportedModelError: If the model isn’t JSON-capable.
        """
        self.provider = provider
        self.model = model
        if self.model not in self._JSON_MODELS:
            raise UnsupportedModelError(f"Model '{self.model}' does not support JSON Mode.")
        self._api_key: Optional[str] = None

    def register_key(self, api_key: str) -> None:
        """
        Register the API key for the chosen provider. Must be called before to_sympy().
        """
        self._api_key = api_key
        if self.provider.lower() == "openai":
            os.environ["OPENAI_API_KEY"] = api_key

    @llm.call(provider="openai", model="gpt-4o-mini", json_mode=True)
    def _mirascope_call(self, prompt: str) -> str:
        """
        Internal Mirascope call in JSON Mode. Overridden at runtime with the chosen provider/model.
        """
        return prompt

    def to_sympy(
        self,
        latex: str,
        context: Optional[str] = None,
        output_notes: bool = False
    ) -> Union[List[sympy.Expr], tuple[List[sympy.Expr], str]]:
        """
        Convert a LaTeX string to Sympy expressions.

        :param latex: The LaTeX to convert.
        :param context: Extra context for the model (optional).
        :param output_notes: If True, also return the model’s notes.
        :returns: A list of Expr, or (exprs, notes).
        :raises APIKeyMissingError: If register_key() wasn’t called.
        :raises StructuredOutputError: On JSON parsing/structure errors.
        :raises EmptyExpressionsError: If the returned "exprs" list is empty.
        :raises SympyConversionError: If sympify fails on any returned string.
        """
        if not self._api_key:
            raise APIKeyMissingError("API key missing; call register_key() first.")

        # Build a prompt that asks strictly for our two keys
        prompt_lines = [
            "Return a JSON object with exactly two keys:",
            '  "exprs": a list of Sympy-parsable strings,',
            '  "notes": a string of assumptions/comments.',
            "",
            f"Latex: {latex}"
        ]
        if context:
            prompt_lines.insert(-1, f"Context: {context}")
        prompt = "\n".join(prompt_lines)

        # Override the decorated call with our chosen provider/model
        call_fn = llm.override(self._mirascope_call,
                               provider=self.provider,
                               model=self.model)
        try:
            response = call_fn(prompt)
            raw = getattr(response, "content", response)
        except Exception as e:
            # Positional arg only
            raise StructuredOutputError(str(e)) from e

        # Parse JSON
        try:
            data = json.loads(raw)
        except Exception as e:
            raise StructuredOutputError(f"Invalid JSON: {e}") from e

        # Validate structure
        if not isinstance(data, dict) or "exprs" not in data or "notes" not in data:
            raise StructuredOutputError(f"Expected keys 'exprs' and 'notes', got: {data}")

        expr_strs = data["exprs"]
        notes = data["notes"]

        if not isinstance(expr_strs, list):
            raise StructuredOutputError(f"'exprs' is not a list: {expr_strs}")
        if len(expr_strs) == 0:
            raise EmptyExpressionsError("No expressions returned by model.")

        # Convert each string to a Sympy Expr
        exprs: List[sympy.Expr] = []
        for expr_str in expr_strs:
            try:
                # sympify only accepts 'locals', not 'globals' :contentReference[oaicite:1]{index=1}
                expr = sympy.sympify(expr_str)
                exprs.append(expr)
            except Exception as e:
                # Positional args for your exception
                raise SympyConversionError(expr_str, str(e)) from e

        return (exprs, notes) if output_notes else exprs
