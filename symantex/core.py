import re
import os
from pydantic import BaseModel
from mirascope import llm
import warnings
import sympy

class Symantex:
    """
    LaTeX-to-Sympy converter using Mirascope in strict JSON mode.
    Only models supporting structured(`json_mode=True`) output will work.

    Usage:
        from symantex import Symantex
        sx = Symantex(provider="openai", model="gpt-4o-mini")
        sx.register_key("your-openai-key")
        expr, multiple, notes = sx.to_sympy(latex, context="...", output_notes=True)
    """
    # Disallow raw TeX commands that could be harmful
    _forbidden_latex = ["\\write", "\\open", "\\input", "\\include"]
    # Known models with JSON support
    _supported_json_models = {
        "openai": [
            "gpt-4o-mini", "gpt-4o", "gpt-4-0613", "gpt-4o-0613", "gpt-4o-2024-08-06"
        ]
    }

    class _Result(BaseModel):
        exprs: list[str]
        notes: str = None

    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini"):
        # Warn if model may not support JSON
        if model not in self._supported_json_models.get(provider, []):
            warnings.warn(
                f"Model '{model}' may not support JSON responses. "
                f"Supported: {self._supported_json_models.get(provider)}"
            )
        self.provider = provider
        self.model = model
        # Single structured call
        @llm.call(
            provider=self.provider,
            model=self.model,
            response_model=Symantex._Result,
            json_mode=True
        )
        def _call(prompt: str) -> Symantex._Result:
            return prompt
        self._call = _call

    def register_key(self, api_key: str):
        if not api_key:
            raise ValueError("API key must be provided")
        os.environ[f"{self.provider.upper()}_API_KEY"] = api_key

    def to_sympy(self, latex: str, context: str = None, output_notes: bool = False):
        """
        Convert LaTeX to Sympy expressions via strict JSON output.

        Returns:
          - expr: Sympy Expr or tuple of Exprs
          - multiple: bool
          - notes: assumptions or error message
        """
        # Check API key
        key_var = f"{self.provider.upper()}_API_KEY"
        if key_var not in os.environ:
            raise RuntimeError(f"API key not set; call register_key() for {self.provider}")
        # Sanitize input
        if any(cmd in latex for cmd in self._forbidden_latex):
            raise ValueError("Disallowed LaTeX command in input")

        # Build JSON-mode prompt
        lines = [
            "You are an expert Python assistant.",
            "Return a JSON object with keys:\n"
            "  exprs: list of Sympy expression strings (no assignment)\n"
            "  notes: assumptions/comments (optional)",
            f"LaTeX: {latex}" 
        ]
        if context:
            lines.insert(2, f"Context: {context}")
        lines.append("Only import from sympy what you need; no markdown fences.")
        prompt = "\n".join(lines)

        # Call the model
        try:
            response = self._call(prompt)
            codes = response.exprs
            notes = response.notes if output_notes else None
        except Exception as e:
            msg = f"Structured output failed: {type(e).__name__}: {e}"
            if output_notes:
                return None, False, msg
            raise RuntimeError(msg)

        if not codes:
            raise ValueError("Model returned no expressions.")

                # Prepare safe globals: only __import__ and sympy namespace
        safe_globals = {"__builtins__": {"__import__": __import__}}
        safe_globals.update({k: getattr(sympy, k) for k in dir(sympy) if not k.startswith("__")})
        # For LaTeX parsing fallback
        from sympy.parsing.latex import parse_latex

        sympy_exprs = []
        for snippet in codes:
            # Clean fences
            text = re.sub(r"^```(?:python)?", "", snippet).rstrip("```")
            # Attempt exec for full control
            code = f"expr = {text}"
            local_vars: dict = {}
            try:
                exec(code, safe_globals, local_vars)
                expr = local_vars.get("expr")
                if expr is None:
                    raise ValueError(f"Snippet did not produce 'expr': {text}")
            except Exception as e:
                # Fallback to sympy.latex parser on original latex
                try:
                    expr = parse_latex(latex)
                    if output_notes:
                        notes = (notes or "") + f" Fallback to parse_latex due to: {type(e).__name__}: {e}"
                except Exception as e2:
                    err = f"Fallback parser error {type(e2).__name__}: {e2}"
                    if output_notes:
                        return None, False, err
                    raise
            sympy_exprs.append(expr)

        multiple = len(sympy_exprs) > 1
        result = tuple(sympy_exprs) if multiple else sympy_exprs[0]
        return result, multiple, notes
