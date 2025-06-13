from sympy import Derivative, Integer, Add
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

# === Chain-rule mixin for n-ary operators ===
@register_property(
    'pull_derivative_chain',
    "Chain-rule derivative: d/dx f(u1,...,un) = Σ_i f(u1,...,u_i',...,un),\n" 
    "with a special case: if no argument depends on x, return f(0,...,0)."
)
class PullDerivativeChainMixin(PropertyMixin):
    """
    Mixin for an n-ary operator f so that:
      d/dx f(u1,...,un) = sum_i f(u1,...,u_i.diff(x),...,un),
    and if all u_i.diff(x) == 0, returns f(0,...,0).
    """
    def _eval_derivative(self, var):
        # Only apply for arity >= 2
        args = list(self.args)
        if len(args) < 2:
            return Derivative(self, var)
        # Compute all derivatives
        diffs = [a.diff(var) for a in args]
        # Special-case: none depend on var
        if all(d == Integer(0) for d in diffs):
            return self.func(*[Integer(0)] * len(args))
        # Otherwise sum chain-rule terms
        terms = []
        for i in range(len(args)):
            new_args = [diffs[j] if j == i else args[j] for j in range(len(args))]
            terms.append(self.func(*new_args))
        return Add(*terms, evaluate=True)

# Patch Derivative.doit to use our chain-rule mixin
register_patch(
    'pull_derivative_chain',
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


    print("Testing Chain Rule")
    from sympy import Derivative as D
    x, y = symbols('x y')

    print("=== Testing chain-rule mixin ===")
    # Binary operator G
    G = build_operator_class('G', ['pull_derivative_chain'], arity=2)
    exprG = D(G(x**2, x**3), x).doit()
    expectedG = G(2*x, x**3) + G(x**2, 3*x**2)
    print(f" d/dx G(x^2, x^3) = {exprG} (expected {expectedG})")
    assert exprG == expectedG

    # Partial on unrelated variable y -> G(0,0)
    exprGy = D(G(x**2, x**3), y).doit()
    expectedGy = G(0, 0)
    print(f" d/dy G(x^2, x^3) = {exprGy} (expected {expectedGy})")
    assert exprGy == expectedGy

    # Ternary operator H
    H = build_operator_class('H', ['pull_derivative_chain'], arity=3)
    exprH = D(H(x, x**2, x**3), x).doit()
    expected_terms = {
        H(Integer(1), x**2, x**3),
        H(x, 2*x, x**3),
        H(x, x**2, 3*x**2)
    }
    print(f" d/dx H(x, x^2, x^3) = {exprH} (expected terms {expected_terms})")
    assert set(exprH.args) == expected_terms

        # Wrong arity: unary should fallback
    U = build_operator_class('U', ['pull_derivative_chain'], arity=1)
    resultU = D(U(x**2), x).doit()
    print(" d/dx U(x^2) fallback yields a Derivative instance")
    assert isinstance(resultU, D)

    # Zero-arity fallback
    R = build_operator_class('R', ['pull_derivative_chain'], arity=0)
    resultR = D(R(), x).doit()
    print(" d/dx R() fallback yields a Derivative instance")
    assert isinstance(resultR, D)

    print("All chain-rule mixin tests passed.")

