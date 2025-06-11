from sympy import Derivative, Add, Integer
from symantex.registry import register_property, register_patch
from symantex.mixins.base import PropertyMixin

# 1) Linear derivative (unary operators)
@register_property(
    'linear_derivative',
    "Unary operator is linear: d/dx f(u(x)) = f(u'(x))."
)
class LinearDerivativeMixin(PropertyMixin):
    """
    Mixin for a unary linear operator f, so that:
      d/dx f(u(x)) = f(u'(x)).
    """
    def _eval_derivative(self, var):
        if len(self.args) != 1:
            return Derivative(self, var)
        inner = self.args[0]
        return self.func(inner.diff(var))

register_patch(
    'linear_derivative',
    Derivative,
    'doit',
    head_attr=lambda deriv: deriv.args[0],
    hook_name='_eval_derivative',
)

# 2) Product rule (binary operators)
@register_property(
    'product_rule',
    "Binary operator satisfies product rule: d/dx f(u,v) = f(u',v) + f(u,v')."
)
class ProductRuleMixin(PropertyMixin):
    """
    Mixin for a binary product-rule operator f, so that:
      d/dx f(u(x), v(x)) = f(u', v) + f(u, v').
    """
    def _eval_derivative(self, var):
        if len(self.args) != 2:
            return Derivative(self, var)
        u, v = self.args
        return self.func(u.diff(var), v) + self.func(u, v.diff(var))

register_patch(
    'product_rule',
    Derivative,
    'doit',
    head_attr=lambda deriv: deriv.args[0],
    hook_name='_eval_derivative',
)

# 3) Chain rule (n-ary operators)
@register_property(
    'pull_derivative_chain',
    "Chain-rule derivative: d/dx f(u1,...,un) = Σ_i f(u1,...,u_i',...,un)."
)
class PullDerivativeChainMixin(PropertyMixin):
    """
    Mixin for an n-ary operator f, so that:
      d/dx f(u1,...,un) = sum_i f(u1,...,u_i',...,un).
    """
    def _eval_derivative(self, var):
        # If operator has no arguments, fallback
        if not self.args:
            return Derivative(self, var)
        # Build each term by differentiating one argument at a time
        terms = []
        for i, arg in enumerate(self.args):
            new_args = [a.diff(var) if j == i else a for j, a in enumerate(self.args)]
            terms.append(self.func(*new_args))
        return Add(*terms, evaluate=True)

register_patch(
    'pull_derivative_chain',
    Derivative,
    'doit',
    head_attr=lambda deriv: deriv.args[0],
    hook_name='_eval_derivative',
)

# 4) Self-tests
if __name__ == "__main__":
    from sympy import symbols, Derivative as D
    from symantex.factory import build_operator_class

    x, y, a, b, c = symbols('x y a b c')

    # Linear derivative tests
    L = build_operator_class('L', ['linear_derivative'], arity=1)
    assert D(L(x**2 + y**3), x).doit() == L(2*x + 0)
    assert D(L(x**2 + y**3), y).doit() == L(0 + 3*y**2)
    assert isinstance(D(build_operator_class('M', ['linear_derivative'], arity=2)(a, b), x).doit(), D)

    # Product rule tests
    P = build_operator_class('P', ['product_rule'], arity=2)
    assert D(P(a*b, b**2), b).doit() == P(a, b**2) + P(a*b, 2*b)
    assert D(P(a*b, b**2), a).doit() == P(b, b**2) + P(a*b, 0)
    assert isinstance(D(build_operator_class('N', ['product_rule'], arity=1)(a*b), b).doit(), D)

    # Chain rule tests
    G2 = build_operator_class('G2', ['pull_derivative_chain'], arity=2)
    expGx = G2(0, b**3) + G2(a**2, 0)
    assert D(G2(a**2, b**3), x).doit() == expGx
    assert D(G2(a**2, b**3), b).doit() == G2(0, b**3) + G2(a**2, 3*b**2)
    assert D(G2(a**2, b**3), y).doit() == expGx
    assert D(G2(a**2, b**3), a).doit() == G2(2*a, b**3) + G2(a**2, 0)

    H3 = build_operator_class('H3', ['pull_derivative_chain'], arity=3)
    result_terms = set(D(H3(a**2, b**2, c**2), b).doit().args)
    expected_terms = {H3(0, b**2, c**2), H3(a**2, 2*b, c**2), H3(a**2, b**2, 0)}
    assert result_terms == expected_terms

    # Zero-arity fallback
    R0 = build_operator_class('R0', ['pull_derivative_chain'], arity=0)
    result_R0 = D(R0(), x).doit()
    assert isinstance(result_R0, D)

    print("All derivative mixin tests passed.")
