# test_symantex.py
import os
import textwrap
import unittest

import sympy
from symantex.core import Symantex

# ---------------------------------------------------------------------------#
API_KEY = os.getenv("SYMANTEX_DEV_KEY")
if API_KEY is None:
    raise unittest.SkipTest("SYMANTEX_DEV_KEY not set; skipping live LLM tests")

# ---------------------------------------------------------------------------#
CASES = [
    # 1 – single, simple fraction
    (r"A = \frac{B}{C}", False),

    # 2 – arg-min training objective (complex)
    (
        r"\theta_{\mathrm{opt}}"
        r"=\underset{\theta \in \Theta}{\operatorname{argmin}}"
        r"\,\frac{1}{N}\sum_{i=1}^{N} L\!\left(\mathcal{N}_{\theta}(\mathbf{u}_{i}),"
        r"\mathbf{y}_{i}\right)",
        False,
    ),

    # 3 – multiple outputs (two equations)
    (
        r"\begin{cases} x^2 + y^2 = 1, \\ x - y = 0 \end{cases}",
        True,
    ),
]

# ---------------------------------------------------------------------------#
class TestSymantexEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sx = Symantex()
        cls.sx.register_key(API_KEY)

    # -------------------------------------------------------------------#
    def _run_case(self, latex: str, expect_multiple: bool) -> None:
        exprs, notes, multiple = self.sx.to_sympy(
            latex,
            output_notes=True,
            failure_logs=True,
            max_retries=1,
        )

        # ----------- Assertions ----------------------------------------
        self.assertIsInstance(notes, str)
        self.assertEqual(multiple, expect_multiple)
        self.assertGreaterEqual(len(exprs), 1)
        if expect_multiple:
            self.assertGreater(len(exprs), 1)

        for e in exprs:
            self.assertIsInstance(e, sympy.Expr)

        # ----------- Pretty print --------------------------------------
        latex_snippet = textwrap.shorten(latex, width=60, placeholder="…")
        print(
            "\n" + "=" * 72,
            f"\nLATEX     : {latex_snippet}",
            f"\nPARSED    : {exprs}",
            f"\nNOTES     : {textwrap.shorten(notes, width=60, placeholder='…')}",
            f"\nMULTIPLE? : {multiple}",
            "\n" + "-" * 72,
        )

    # -------------------------------------------------------------------#
    def test_all_cases(self) -> None:
        for latex, expect_multiple in CASES:
            with self.subTest(latex=latex[:40] + "..."):
                self._run_case(latex, expect_multiple)


# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    # Use higher verbosity so unittest prints sub-test names
    unittest.main(verbosity=2)
