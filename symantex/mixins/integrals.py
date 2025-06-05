# File: symantex/mixins/integrals.py

"""
Integral‐related mixins, using the registry’s patch system to override
sympy.Integral.doit when a custom operator has an integral property.
Includes:
  - pull_integral        (pull integral inside operator)
  - distribute_integral  (distribute integral over each argument)
"""

from sympy import Integral, Integer
from sympy.core.basic import Basic
from symantex.registry import register_property, register_patch
from symantex.mixins.base import PropertyMixin


@register_property(
    'pull_integral',
    "Pull integral inside the operator: ∫ f(u(x)) dx → f( ∫ u(x) dx )."
)
class PullIntegralMixin(PropertyMixin):
    """
    Mixin for a unary (or n‐ary) operator f, so that:
      Integral(f(u1, u2, …), x).doit() = f( Integral(u1, x).doit(), Integral(u2, x).doit(), … ).
    """
    def _eval_integral(self, sym, **kwargs):
        # If operator has no arguments, fallback to default Integral
        if not self.args:
            return Integral(self, sym)
        evaluated_args = []
        for arg in self.args:
            inner = Integral(arg, sym).doit()
            evaluated_args.append(inner)
        return self.func(*evaluated_args)


register_patch(
    'pull_integral',
    Integral,
    'doit',
    '_eval_integral',
    # head_attr: the “inside” operator is always args[0] of Integral
    lambda self: self.args[0]
)


@register_property(
    'distribute_integral',
    "Distribute integral across each argument: ∫ f(a, b) dx → f( ∫ a dx, ∫ b dx )."
)
class DistributeIntegralMixin(PropertyMixin):
    """
    Mixin for a binary (or n‐ary) operator f, so that:
      Integral(f(a, b, …), x).doit() = f( Integral(a, x).doit(), Integral(b, x).doit(), … ).
    """
    def _eval_integral(self, sym, **kwargs):
        # If operator has no arguments, fallback
        if not self.args:
            return Integral(self, sym)
        evaluated_args = [Integral(arg, sym).doit() for arg in self.args]
        return self.func(*evaluated_args)


register_patch(
    'distribute_integral',
    Integral,
    'doit',
    '_eval_integral',
    lambda self: self.args[0]
)


if __name__ == "__main__":
    """
    Tests for integral mixins. Run via:
        python symantex/mixins/integrals.py
    """
    import sympy
    from sympy import Symbol
    from symantex.factory import build_operator_class

    x, a, b = Symbol('x'), Symbol('a'), Symbol('b')

    print("=== Testing pull_integral mixin ===")
    # 1) Unary operator U with pull_integral
    U = build_operator_class('U', ['pull_integral'], arity=1)
    expr_U = Integral(U(x**2), x)
    result_U = expr_U.doit()
    print(f"Integral(U(x^2), x).doit() → {result_U}  (expected U(x^3/3))")
    assert result_U == U(x**3/3)

    # 2) Operator V built with pull_integral but wrong arity (arity=2)
    V = build_operator_class('V', ['pull_integral'], arity=2)
    expr_V = Integral(V(a, b), a)
    result_V = expr_V.doit()
    print(f"Integral(V(a, b), a).doit() → {result_V}  (expected Integral(V(a, b), a))")
    assert isinstance(result_V, sympy.Integral)

    # 3) Without mixin: W is plain unary
    W = build_operator_class('W', [], arity=1)
    expr_W = Integral(W(x**3), x)
    result_W = expr_W.doit()
    print(f"(No mixin) Integral(W(x^3), x).doit() → {result_W}  (expected Integral(W(x^3), x))")
    assert isinstance(result_W, sympy.Integral)

    print("\n=== Testing distribute_integral mixin ===")
    # 4) Binary operator P with distribute_integral
    P = build_operator_class('P', ['distribute_integral'], arity=2)
    expr_P = Integral(P(a, b), a)
    # ∫a dx = a^2/2, ∫b dx = b*a
    expected_P = P(a**2/2, b*a)
    result_P = expr_P.doit()
    print(f"Integral(P(a, b), a).doit() → {result_P}  (expected {expected_P})")
    assert result_P == expected_P

    # 5) Operator Q built with distribute_integral but wrong arity (arity=1)
    Q = build_operator_class('Q', ['distribute_integral'], arity=1)
    expr_Q = Integral(Q(a), a)
    result_Q = expr_Q.doit()
    print(f"Integral(Q(a), a).doit() → {result_Q}  (expected Integral(Q(a), a))")
    assert isinstance(result_Q, sympy.Integral)

    # 6) Without mixin: R is plain binary
    R = build_operator_class('R', [], arity=2)
    expr_R = Integral(R(a, b), a)
    result_R = expr_R.doit()
    print(f"(No mixin) Integral(R(a, b), a).doit() → {result_R}  (expected Integral(R(a, b), a))")
    assert isinstance(result_R, sympy.Integral)

    print("\n=== Combined tests ===")
    # 7) Operator S with both pull_integral and distribute_integral
    S = build_operator_class('S', ['pull_integral', 'distribute_integral'], arity=2)
    expr_S1 = Integral(S(a + b, a*b), a)
    # Because 'pull_integral' and 'distribute_integral' both do the same for a two‐arg function,
    # we expect: ∫(a+b) dx = a^2/2 + a*b, ∫(a*b) dx = a^2*b/2
    expected_S1 = S((a + b).integrate(a), (a*b).integrate(a))
    result_S1 = expr_S1.doit()
    print(f"Integral(S(a+b, a*b), a) → {result_S1}  (expected {expected_S1})")
    assert result_S1 == expected_S1

    print("\nAll integral mixin tests passed.")
