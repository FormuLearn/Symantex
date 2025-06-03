from sympy import Derivative
from sympy.core.basic import Basic
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property(
    'pull_derivative_chain',
    "Chain-rule derivative: returns sum of functions with each argument replaced by its derivative."
)
class PullsDerivativeChainMixin(PropertyMixin):
    """
    Mixin that applies the chain rule: for each argument, replaces that slot with its derivative (even if zero) and sums all resulting terms.
    Example: d/da G(a^2, b^3) -> G(2*a, b^3) + G(a^2, 0).
    """
    def _eval_derivative(self, sym):
        terms = []
        for i, arg in enumerate(self.args):
            # Compute derivative of this argument (could be zero)
            arg_deriv = arg.diff(sym)
            new_args = list(self.args)
            new_args[i] = arg_deriv
            terms.append(self.func(*new_args))
        # If no argument depends on sym, sum will be all zeros -> fallback
        return sum(terms) if terms else Derivative(self, sym)

@register_property(
    'pull_derivative_unevaluated',
    "Pull derivative inside, keeping unevaluated Derivative for independent slots."
)
class PullsDerivativeUnevaluatedMixin(PropertyMixin):
    """
    Mixin that pulls derivative inside each argument without simplifying zeros.
    Replaces each dependent argument with an UnevaluatedExpr of Derivative(arg, sym, evaluate=False),
    leaves independent arguments unchanged.
    Example: d/da G(a^2, b^3) -> G(UnevaluatedExpr(Derivative(a^2, a)), b^3).
    """
    def _eval_derivative(self, sym):
        from sympy import UnevaluatedExpr
        new_args = []
        for arg in self.args:
            if arg.has(sym):
                new_args.append(UnevaluatedExpr(Derivative(arg, sym, evaluate=False)))
            else:
                new_args.append(arg)
        return self.func(*new_args)

if __name__ == "__main__":
    # Tests for derivatives mixins
    from symantex.factory import build_operator_class
    from sympy import Symbol, Derivative

    x, a, b = Symbol('x'), Symbol('a'), Symbol('b')

    # Chain-rule mixin test
    F_chain = build_operator_class('F_chain', ['pull_derivative_chain'], arity=1)
    u = x**2
    expr_c = Derivative(F_chain(u), x)
    print(f"Derivative(F_chain(u), x): {expr_c}")
    result_c = expr_c.doit()
    print(f"Result after doit: {result_c}")  # Expect F_chain(2*x)

    G_chain = build_operator_class('G_chain', ['pull_derivative_chain'], arity=2)
    expr_gc = Derivative(G_chain(a**2, b**3), a)
    print(f"Derivative(G_chain(a**2, b**3), a): {expr_gc}")
    result_gc = expr_gc.doit()
    print(f"Result after doit: {result_gc}")  # Expect G_chain(2*a, b**3) + G_chain(a**2, 0)

    # Unevaluated-pull mixin test
    F_uneq = build_operator_class('F_uneq', ['pull_derivative_unevaluated'], arity=1)
    expr_u = Derivative(F_uneq(u), x)
    print(f"Derivative(F_uneq(u), x): {expr_u}")
    result_u = expr_u.doit()
    print(f"Result after doit: {result_u}")  # Expect F_uneq(Derivative(x**2, x))

    G_uneq = build_operator_class('G_uneq', ['pull_derivative_unevaluated'], arity=2)
    expr_gu = Derivative(G_uneq(a**2, b**3), a)
    print(f"Derivative(G_uneq(a**2, b**3), a): {expr_gu}")
    result_gu = expr_gu.doit()
    print(f"Result after doit: {result_gu}")  # Expect G_uneq(Derivative(a**2, a), b**3)
