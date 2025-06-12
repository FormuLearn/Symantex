# example_usage.py

import os
from symantex.core import Symantex
from symantex.errors import (
    APIKeyMissingError,
    UnsupportedModelError,
    StructuredOutputError,
    EmptyExpressionsError,
    SympyConversionError
)

def main():
    # 1. Grab your dev key from the environment
    api_key = os.getenv("SYMANTEX_DEV_KEY")
    if not api_key:
        raise RuntimeError("Please set SYMANTEX_DEV_KEY in your environment.")

    # 2. Initialize Symantex and register the key
    try:
        sx = Symantex(provider="openai", model="gpt-4o-mini")
    except UnsupportedModelError as e:
        print("Model error:", e)
        return

    sx.register_key(api_key)

    # 3. A list of test LaTeX inputs
    tests = [
        r"x^2 + 2x + 1",
        r"\frac{d}{dx} \sin(x)",
        r"\int_0^\infty e^{-x}\,dx",
    ]

    # 4. Run through them
    for latex in tests:
        print(f"\n=== LaTeX: {latex}")
        try:
            # simple conversion
            exprs = sx.to_sympy(latex)
            for e in exprs:
                print("  →", e, "  (type:", type(e).__name__, ")")
        except (APIKeyMissingError, StructuredOutputError,
                EmptyExpressionsError, SympyConversionError) as e:
            print("  [Error]", type(e).__name__, e)

    # 5. Example with context and notes
    print("\n=== With context & notes")
    latex = r"\sin^2(x) + \cos^2(x)"
    try:
        exprs, notes = sx.to_sympy(latex,
                                   context="Verify the Pythagorean identity",
                                   output_notes=True)
        print("  Expressions:", exprs)
        print("  Notes from model:", notes)
    except Exception as e:
        print("  [Error]", type(e).__name__, e)


if __name__ == "__main__":
    main()
