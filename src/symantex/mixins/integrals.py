# File: symantex/mixins/integrals.py

"""
Integral‐related mixins, using the registry’s patch system to override
sympy.Integral.doit when a custom operator has an integral property.
Includes:
  - pull_integral        (pull integral inside a *unary* operator)
  - distribute_integral  (distribute integral over each argument of an n‐ary operator, n≥2)
"""

from sympy import Integral
from sympy.integrals.integrals import Integral as _BaseIntegral
from sympy.core.basic import Basic
from sympy import Integer
from symantex.registry import register_property, register_patch
from symantex.mixins.base import PropertyMixin


@register_property(
    'pull_integral',
    "Pull integral inside a *unary* operator: ∫ f(u(x)) dx → f( ∫ u(x) dx )."
)
class PullIntegralMixin(PropertyMixin):
    """
    Mixin for a *unary* operator f, so that:
      Integral(f(u(x)), x).doit() = f( Integral(u(x), x).doit() ).

    If the operator has not exactly one argument, we must return a plain Integral(self, x)
    without invoking this same hook (to avoid infinite recursion).  We accomplish that
    by temporarily deleting PullIntegralMixin._eval_Integral from the mixin class itself,
    forcing Sympy’s Integral.__new__ to skip our hook.
    """
    def _eval_Integral(self, sym, **kwargs):
        # Only “pull the integral inside” when exactly one argument is present.
        if len(self.args) != 1:
            # Wrong arity → fallback to a plain Integral(self, sym).
            # To prevent recursion, temporarily delete this mixin’s _eval_Integral.
            mixin_cls = PullIntegralMixin
            orig = getattr(mixin_cls, "_eval_Integral", None)
            # Remove it from the class (so that Sympy’s Integral.__new__ will not see it)
            delattr(mixin_cls, "_eval_Integral")
            try:
                raw = _BaseIntegral(self, sym)
            finally:
                # Restore the mixin method
                setattr(mixin_cls, "_eval_Integral", orig)
            return raw

        # Arity == 1: pull the integral inside
        inner = self.args[0]
        inner_val = Integral(inner, sym).doit()
        return self.func(inner_val)


register_patch(
    'pull_integral',
    Integral,
    'doit',
    '_eval_Integral',
    # head_attr: the “operator inside” is always args[0] of Integral.
    lambda self: self.args[0]
)


@register_property(
    'distribute_integral',
    "Distribute integral across each argument of an *n‐ary* operator (n ≥ 2): "
    "∫ f(a, b, …) dx → f( ∫ a dx, ∫ b dx, … )."
)
class DistributeIntegralMixin(PropertyMixin):
    """
    Mixin for a binary (or n‐ary, with n ≥ 2) operator f, so that:
      Integral(f(u1, u2, …, un), x).doit()
        = f( Integral(u1, x).doit(), Integral(u2, x).doit(), …, Integral(un, x).doit() ).

    If the operator has fewer than two arguments, we return a plain Integral(self, x)
    (again avoiding infinite recursion by temporarily removing our own _eval_Integral).
    """
    def _eval_Integral(self, sym, **kwargs):
        # Only “distribute” when two or more arguments exist.
        if len(self.args) < 2:
            mixin_cls = DistributeIntegralMixin
            orig = getattr(mixin_cls, "_eval_Integral", None)
            delattr(mixin_cls, "_eval_Integral")
            try:
                raw = _BaseIntegral(self, sym)
            finally:
                setattr(mixin_cls, "_eval_Integral", orig)
            return raw

        # Arity ≥ 2: distribute the integral across each argument
        evaluated_args = [Integral(arg, sym).doit() for arg in self.args]
        return self.func(*evaluated_args)


register_patch(
    'distribute_integral',
    Integral,
    'doit',
    '_eval_Integral',
    lambda self: self.args[0]
)


if __name__ == "__main__":
    """
    Tests for integral mixins.  Run via:
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
    expected_U = U(x**3/3)
    print(f" Integral(U(x^2), x).doit() → {result_U}   (expected {expected_U})")
    assert result_U == expected_U

    # 2) Operator V with pull_integral but WRONG ARITY (arity=2) → plain Integral
    V = build_operator_class('V', ['pull_integral'], arity=2)
    expr_V = Integral(V(a, b), a)
    result_V = expr_V.doit()
    print(f" Integral(V(a, b), a).doit() → {result_V}   "
          f"(expected Integral(V(a, b), a))")
    assert isinstance(result_V, sympy.Integral)

    # 3) Operator W WITHOUT mixin (arity=1) → plain Integral
    W = build_operator_class('W', [], arity=1)
    expr_W = Integral(W(x**3), x)
    result_W = expr_W.doit()
    print(f" (No mixin) Integral(W(x^3), x).doit() → {result_W}   "
          f"(expected Integral(W(x^3), x))")
    assert isinstance(result_W, sympy.Integral)

    print("\n=== Testing distribute_integral mixin ===")
    # 4) Binary operator P with distribute_integral
    P = build_operator_class('P', ['distribute_integral'], arity=2)
    expr_P = Integral(P(a, b), a)
    # ∫ a dx = a**2/2 ;  ∫ b dx = a*b
    expected_P = P(a**2/2, a*b)
    result_P = expr_P.doit()
    print(f" Integral(P(a, b), a).doit() → {result_P}   (expected {expected_P})")
    assert result_P == expected_P

    # 5) Operator Q with distribute_integral but WRONG ARITY (arity=1) → plain Integral
    Q = build_operator_class('Q', ['distribute_integral'], arity=1)
    expr_Q = Integral(Q(a), a)
    result_Q = expr_Q.doit()
    print(f" Integral(Q(a), a).doit() → {result_Q}   (expected Integral(Q(a), a))")
    assert isinstance(result_Q, sympy.Integral)

    # 6) Operator R WITHOUT mixin (arity=2) → plain Integral
    R = build_operator_class('R', [], arity=2)
    expr_R = Integral(R(a, b), a)
    result_R = expr_R.doit()
    print(f" (No mixin) Integral(R(a, b), a).doit() → {result_R}   "
          f"(expected Integral(R(a, b), a))")
    assert isinstance(result_R, sympy.Integral)

    print("\n=== Combined pull_integral + distribute_integral ===")
    # 7) Operator S with both pull_integral and distribute_integral (arity=2)
    S = build_operator_class('S', ['pull_integral','distribute_integral'], arity=2)
    expr_S1 = Integral(S(a + b, a*b), a)
    expected_S1 = S((a + b).integrate(a), (a*b).integrate(a))
    result_S1 = expr_S1.doit()
    print(f" Integral(S(a+b, a*b), a).doit() → {result_S1}   (expected {expected_S1})")
    assert result_S1 == expected_S1

    print("\nAll integral mixin tests passed.")
