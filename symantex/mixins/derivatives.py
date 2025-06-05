# File: symantex/mixins/derivatives.py

"""
Derivative‐related mixins, using the registry’s patch system to override
sympy.Derivative.doit when a custom operator has a derivative property.
Includes:
  - linear_derivative       (unary linear operators)
  - product_rule            (binary product‐rule operators)
  - pull_derivative_chain   (n‐ary chain‐rule pull operators)
"""

from sympy import Derivative, Add, Integer
from sympy.core.basic import Basic
from symantex.registry import register_property, register_patch
from symantex.mixins.base import PropertyMixin


@register_property(
    'linear_derivative',
    "Unary operator is linear: d/dx f(u(x)) = f(d/dx u(x))."
)
class LinearDerivativeMixin(PropertyMixin):
    """
    Mixin for a unary Linear operator f, so that:
      d/dx f(u(x)) = f( u'(x) ).
    """
    def _eval_derivative(self, sym):
        # Expect exactly one argument
        if len(self.args) != 1:
            # If arity mismatched, do not handle—fallback to original Derivative
            return Derivative(self, sym)
        arg = self.args[0]
        # Compute derivative of inner argument
        arg_deriv = arg.diff(sym)
        return self.func(arg_deriv)


register_patch(
    'linear_derivative',
    Derivative,
    'doit',
    '_eval_derivative',
    'expr'
)


@register_property(
    'product_rule',
    "Binary operator satisfies product rule: d/dx f(u,v) = f(u', v) + f(u, v')."
)
class ProductRuleMixin(PropertyMixin):
    """
    Mixin for a binary Product‐rule operator f, so that:
      d/dx f(u(x), v(x)) = f(u'(x), v(x)) + f(u(x), v'(x)).
    """
    def _eval_derivative(self, sym):
        # Only apply if exactly two arguments
        if len(self.args) != 2:
            return Derivative(self, sym)
        u, v = self.args
        u_deriv = u.diff(sym)
        v_deriv = v.diff(sym)
        term1 = self.func(u_deriv, v)
        term2 = self.func(u, v_deriv)
        return term1 + term2


register_patch(
    'product_rule',
    Derivative,
    'doit',
    '_eval_derivative',
    'expr'
)


@register_property(
    'pull_derivative_chain',
    "Chain‐rule derivative: sum of operator applied to each argument replaced by its derivative."
)
class PullDerivativeChainMixin(PropertyMixin):
    """
    Mixin for an n‐ary operator f, so that:
      d/dx f(u1, u2, ..., un) = Σ_i f(u1, ..., u_i', ..., un).
    """
    def _eval_derivative(self, sym):
        # If no arguments, fallback
        if not self.args:
            return Derivative(self, sym)
        terms = []
        for i, arg in enumerate(self.args):
            arg_deriv = arg.diff(sym)
            new_args = list(self.args)
            new_args[i] = arg_deriv
            terms.append(self.func(*new_args))
        return Add(*terms, evaluate=True)


register_patch(
    'pull_derivative_chain',
    Derivative,
    'doit',
    '_eval_derivative',
    'expr'
)


if __name__ == "__main__":
    """
    Tests for derivative mixins. Run via:
        python symantex/mixins/derivatives.py
    """
    import sympy
    from sympy import Symbol
    from symantex.factory import build_operator_class

    x, a, b, c = Symbol('x'), Symbol('a'), Symbol('b'), Symbol('c')

    print("=== Testing linear_derivative mixin ===")
    # 1) Correct arity: unary operator L
    L = build_operator_class('L', ['linear_derivative'], arity=1)
    expr_L = Derivative(L(x**2), x)
    result_L = expr_L.doit()
    print(f"Derivative(L(x^2), x) → {result_L}  (expected L(2*x))")
    assert result_L == L(2*x)

    # 2) Wrong arity: operator M built with linear_derivative but arity=2
    M = build_operator_class('M', ['linear_derivative'], arity=2)
    expr_M = Derivative(M(a, b), a)
    result_M = expr_M.doit()
    print(f"Derivative(M(a,b), a) → {result_M}  (expected Derivative(...))")
    assert isinstance(result_M, sympy.Derivative)

    # 3) Without mixin: K is plain unary
    K = build_operator_class('K', [], arity=1)
    expr_K = Derivative(K(x**3), x)
    result_K = expr_K.doit()
    print(f"(No mixin) Derivative(K(x^3), x) → {result_K}  (expected Derivative(...))")
    assert isinstance(result_K, sympy.Derivative)

    print("\n=== Testing product_rule mixin ===")
    # 4) Correct arity: binary operator P
    P = build_operator_class('P', ['product_rule'], arity=2)
    u, v = a*b, b**2
    expr_P = Derivative(P(u, v), b)
    expected_P = P(a, b**2) + P(a*b, 2*b)
    result_P = expr_P.doit()
    print(f"Derivative(P(a*b, b^2), b) → {result_P}  (expected {expected_P})")
    assert result_P == expected_P

    # 5) Wrong arity: operator N has product_rule but arity=1
    N = build_operator_class('N', ['product_rule'], arity=1)
    expr_N = Derivative(N(a*b), b)
    result_N = expr_N.doit()
    print(f"Derivative(N(a*b), b) → {result_N}  (expected Derivative(...))")
    assert isinstance(result_N, sympy.Derivative)

    # 6) Without mixin: Q is plain binary
    Q = build_operator_class('Q', [], arity=2)
    expr_Q = Derivative(Q(u, v), b)
    result_Q = expr_Q.doit()
    print(f"(No mixin) Derivative(Q(a*b, b^2), b) → {result_Q}  (expected Derivative(...))")
    assert isinstance(result_Q, sympy.Derivative)

    print("\n=== Testing pull_derivative_chain mixin ===")
    # 7) Binary chain‐rule
    G = build_operator_class('G', ['pull_derivative_chain'], arity=2)
    expr_G = Derivative(G(a**2, b**3), a)
    # Expected: G(2*a, b^3) + G(a^2, 0)
    expected_G = G(2*a, b**3) + G(a**2, Integer(0))
    result_G = expr_G.doit()
    print(f"Derivative(G(a^2, b^3), a) → {result_G}  (expected {expected_G})")
    assert result_G == expected_G

    # 8) Ternary chain‐rule (arity=3)
    H = build_operator_class('H', ['pull_derivative_chain'], arity=3)
    expr_H = Derivative(H(a**2, b**2, c**2), b)

    # Correct expected terms:
    expected_terms = {
        H(Integer(0),   b**2,     c**2),    # derivative of a^2 is 0
        H(a**2,         2*b,      c**2),    # derivative of b^2 is 2*b
        H(a**2,         b**2,     Integer(0))  # derivative of c^2 is 0
    }

    result_H = expr_H.doit()
    print(
        f"Derivative(H(a^2, b^2, c^2), b) → {result_H}\n"
        f"Expected (unordered) = {expected_terms}"
    )

    result_terms = set(result_H.args) if isinstance(result_H, Add) else {result_H}
    assert result_terms == expected_terms


    # 9) Wrong arity: operator R has pull_derivative_chain but arity=0
    R = build_operator_class('R', ['pull_derivative_chain'], arity=0)
    expr_R = Derivative(R(), x)
    result_R = expr_R.doit()
    print(f"Derivative(R(), x) → {result_R}  (expected Derivative(...))")
    assert isinstance(result_R, sympy.Derivative)

    # 10) Without mixin: S is plain binary
    S = build_operator_class('S', [], arity=2)
    expr_S = Derivative(S(a**2, b**2), a)
    result_S = expr_S.doit()
    print(f"(No mixin) Derivative(S(a^2, b^2), a) → {result_S}  (expected Derivative(...))")
    assert isinstance(result_S, sympy.Derivative)

    print("\nAll derivative mixin tests passed.")
