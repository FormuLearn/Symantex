# mixins/integrals.py

from sympy import Integral, UnevaluatedExpr
from sympy.core.basic import Basic
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin


@register_property(
    'pull_integral',
    "Pull integral inside the function: Integral(f(u), x) -> f(Integral(u, x).doit())"
)
class PullsIntegralMixin(PropertyMixin):
    """
    Mixin that pulls the integral inside each argument of the function,
    immediately calling .doit() on the inner Integral.

    For example:
      Integral(F(u), x).doit()  →  F(Integral(u, x).doit())
    so if u = x**2, you get F(x**3/3).
    """
    def _eval_Integral(self, sym, **kwargs):
        # For each argument, compute Integral(arg, sym).doit() and then call the function
        evaluated_args = []
        for arg in self.args:
            inner = Integral(arg, sym).doit()
            evaluated_args.append(inner)
        return self.func(*evaluated_args)


@register_property(
    'distribute_integral',
    "Distribute integral across all function arguments: \
     Integral(f(a, b), x) -> f(Integral(a, x).doit(), Integral(b, x).doit())"
)
class DistributeIntegralMixin(PropertyMixin):
    """
    Mixin that distributes the integral to each argument, fully evaluating each,
    and then calls the function with those evaluated slots.

    Example:
      Integral(G(a, b), x).doit()  →  G(Integral(a, x).doit(), Integral(b, x).doit()).
    """
    def _eval_Integral(self, sym, **kwargs):
        evaluated_args = [Integral(arg, sym).doit() for arg in self.args]
        return self.func(*evaluated_args)


if __name__ == "__main__":
    # Tests for integrals mixins
    from symantex.factory import build_operator_class
    from sympy import Symbol, Integral

    x, a, b = Symbol('x'), Symbol('a'), Symbol('b')

    # 1) PullsIntegralMixin for single argument
    #    Expect: Integral(F(u), x).doit() → F(x**3/3)
    F = build_operator_class('F', ['pull_integral'], arity=1)
    u = x**2
    expr = Integral(F(u), x)
    print(f"Integral(F(u), x): {expr}")
    result = expr.doit()
    print(f"Result after doit: {result}")  # → F(x**3/3)

    # 2) PullsIntegralMixin for two arguments
    #    Expect: Integral(G(a, b), a).doit() → G(Integral(a,a).doit(), Integral(b,a).doit())
    #    Since Integral(a, a).doit() = a**2/2,  Integral(b, a).doit() = b*a
    G = build_operator_class('G', ['pull_integral'], arity=2)
    expr2 = Integral(G(a, b), a)
    print(f"Integral(G(a, b), a): {expr2}")
    result2 = expr2.doit()
    print(f"Result after doit: {result2}")  # → G(a**2/2, b*a)

    # 4) DistributeIntegralMixin for two arguments
    #    Expect: Integral(K(a, b), a).doit() → K(a**2/2, b*a)
    #    i.e. same result as pull_integral for this example
    K = build_operator_class('K', ['distribute_integral'], arity=2)
    expr_k = Integral(K(a, b), a)
    print(f"Integral(K(a, b), a): {expr_k}")
    result_k = expr_k.doit()
    print(f"Result after doit: {result_k}")  # → K(a**2/2, b*a)

    print("Integrals mixin tests passed.")
