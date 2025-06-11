from sympy import Derivative, Integer
from sympy.core.function import UndefinedFunction
from symantex.registry import register_property, register_patch
from symantex.mixins.base import PropertyMixin

# === 1) Linear derivative (unary operators) ===
@register_property(
    'linear_derivative',
    "Unary operator is linear: d/dx f(u(x)) = f(u'(x))."
)
class LinearDerivativeMixin(PropertyMixin):
    """
    Mixin for a unary operator f so that:
      d/dx f(u(x)) = f(u'(x)).
    """
    def _eval_derivative(self, var):
        # Only apply if single argument
        if len(self.args) != 1:
            return Derivative(self, var)
        inner = self.args[0]
        return self.func(inner.diff(var))

# Patch Derivative.doit for linear_derivative
register_patch(
    'linear_derivative',
    Derivative,
    'doit',
    head_attr=lambda deriv: deriv.args[0] if deriv.args else None,
    hook_name='_eval_derivative',
)

# === 2) Product rule (binary operators) ===
@register_property(
    'product_rule',
    "Binary operator satisfies product rule: d/dx f(u,v) = f(u',v) + f(u,v')."
)
class ProductRuleMixin(PropertyMixin):
    """
    Mixin for a binary operator f so that:
      d/dx f(u(x),v(x)) = f(u',v) + f(u,v').
    """
    def _eval_derivative(self, var):
        # Only apply if exactly two arguments
        if len(self.args) != 2:
            return Derivative(self, var)
        u, v = self.args
        return self.func(u.diff(var), v) + self.func(u, v.diff(var))

# Patch Derivative.doit for product_rule
register_patch(
    'product_rule',
    Derivative,
    'doit',
    head_attr=lambda deriv: deriv.args[0] if deriv.args else None,
    hook_name='_eval_derivative',
)

# === Self-tests ===
if __name__ == "__main__":
    from sympy import symbols
    from symantex.factory import build_operator_class

    x, a, b = symbols('x a b')

    print("=== Testing linear_derivative mixin ===")
    # Unary operator L
    L = build_operator_class('L', ['linear_derivative'], arity=1)
    # Correct: derivative of L(x^2) wrt x -> L(2*x)
    result_L = Derivative(L(x**2), x).doit()
    expected_L = L(2*x)
    print(f" d/dx L(x^2) = {result_L} (expected {expected_L})")
    assert result_L == expected_L
    # Wrong arity: M has two args, should fallback
    M = build_operator_class('M', ['linear_derivative'], arity=2)
    result_M = Derivative(M(a, b), a).doit()
    print(f" d/da M(a,b) fallback = {result_M}")
    assert isinstance(result_M, Derivative)
    print("linear_derivative tests passed.\n")

    print("=== Testing product_rule mixin ===")
    # Binary operator P
    P = build_operator_class('P', ['product_rule'], arity=2)
    expr_P = Derivative(P(a*b, b**2), b).doit()
    expected_P = P(a, b**2) + P(a*b, 2*b)
    print(f" d/db P(a*b, b^2) = {expr_P} (expected {expected_P})")
    assert expr_P == expected_P
    # Wrong arity: N has one arg, should fallback
    N = build_operator_class('N', ['product_rule'], arity=1)
    result_N = Derivative(N(a*b), b).doit()
    print(f" d/db N(a*b) fallback = {result_N}")
    assert isinstance(result_N, Derivative)
    print("product_rule tests passed.\n")

    print("All linear + product_rule mixin tests passed.")
