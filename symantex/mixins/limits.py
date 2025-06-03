# File: symantex/mixins/limits.py

from sympy import Limit
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property(
    'pull_limit',
    "Pull limit inside the function: "
    "limₓ→a F(u₁(x), …, uₙ(x)) = F(limₓ→a u₁(x), …, limₓ→a uₙ(x))"
)
class PullsLimitMixin(PropertyMixin):
    """
    Mixin for a Function‐class F so that 
    Limit(F(arg1, arg2, …), var, point, dir).doit()
    becomes F(Limit(arg1, var, point, dir).doit(), …).
    """
    def _eval_limit(self, var, point, dir="+", **kwargs):
        evaluated_args = [
            Limit(arg, var, point, dir).doit(**kwargs)
            for arg in self.args
        ]
        return self.func(*evaluated_args)


@register_property(
    'distribute_limit',
    "Distribute limit across each argument: "
    "limₓ→a G(a,b) = G(limₓ→a a, limₓ→a b)."
)
class DistributeLimitMixin(PropertyMixin):
    """
    Mixin for a Function‐class G so that 
    Limit(G(arg1, arg2), var, point, dir).doit()
    becomes G(Limit(arg1, var, point, dir).doit(), Limit(arg2, var, point, dir).doit()).
    """
    def _eval_limit(self, var, point, dir="+", **kwargs):
        evaluated_args = [
            Limit(arg, var, point, dir).doit(**kwargs)
            for arg in self.args
        ]
        return self.func(*evaluated_args)

if __name__ == "__main__":
    # === Simple tests for pull_limit and distribute_limit mixins ===

    from sympy import Symbol, Limit, oo, sin, AccumBounds
    from symantex.factory import build_operator_class

    x, a, b = Symbol('x'), Symbol('a'), Symbol('b')

    # Test 1: pull_limit on a single-argument function
    # Expect: lim_{x→0} F_pull(x**2) = F_pull(0)
    F_pull = build_operator_class('F_pull', ['pull_limit'], arity=1)
    expr1 = Limit(F_pull(x**2), x, 0)
    print(f"Test 1 Before .doit(): {expr1}")
    result1 = expr1.doit()
    print(f"Test 1 After  .doit(): {result1}")
    assert str(result1) == "F_pull(0)"

    # Test 2: distribute_limit on a two-argument function
    # Expect: lim_{x→∞} G_dist(1/x, x + 2) = G_dist(0, oo)
    G_dist = build_operator_class('G_dist', ['distribute_limit'], arity=2)
    expr2 = Limit(G_dist(1/x, x + 2), x, oo)
    print(f"Test 2 Before .doit(): {expr2}")
    result2 = expr2.doit()
    print(f"Test 2 After  .doit(): {result2}")
    assert str(result2) == "G_dist(0, oo)"

    # Test 3: pull_limit combined with a standard limit Sympy knows
    # Expect: lim_{x→0} F2(sin(x)/x) = F2(1)
    F2 = build_operator_class('F2', ['pull_limit'], arity=1)
    expr3 = Limit(F2(sin(x)/x), x, 0)
    print(f"Test 3 Before .doit(): {expr3}")
    result3 = expr3.doit()
    print(f"Test 3 After  .doit(): {result3}")
    assert str(result3) == "F2(1)"

    # Test 4: one-sided limit with pull_limit
    # Expect: lim_{x→1^+} F3(1/(x - 1)) = F3(oo)
    F3 = build_operator_class('F3', ['pull_limit'], arity=1)
    expr4 = Limit(F3(1/(x - 1)), x, 1, dir="+")
    print(f"Test 4 Before .doit(): {expr4}")
    result4 = expr4.doit()
    print(f"Test 4 After  .doit(): {result4}")
    assert str(result4) == "F3(oo)"

    # ------------------------------------------------------------
    # Test 5: Compare “no mixin” vs. “with pull_limit mixin” for a simple inner limit
    #
    #   5a) H(x**2) has no _eval_limit, so Limit(H(x**2), x, 0).doit() remains unevaluated.
    #   5b) F_pull(x**2) has pull_limit, so Limit(F_pull(x**2), x, 0).doit() → F_pull(0).

    from sympy import Function

    H = Function('H')  # plain Sympy Function, no mixin

    expr5a = Limit(H(x**2), x, 0)
    print(f"Test 5a (no mixin) Before .doit(): {expr5a}")
    result5a = expr5a.doit()
    print(f"Test 5a (no mixin) After  .doit(): {result5a}")
    # Since H has no _eval_limit, Sympy cannot simplify, so it stays as a Limit
    assert isinstance(result5a, type(expr5a)) and result5a == expr5a, (
        f"Expected unevaluated Limit, got {result5a}"
    )

    expr5b = Limit(F_pull(x**2), x, 0)
    print(f"Test 5b (with mixin) Before .doit(): {expr5b}")
    result5b = expr5b.doit()
    print(f"Test 5b (with mixin) After  .doit(): {result5b}")
    # With pull_limit mixin, Sympy calls _eval_limit → F_pull(0)
    assert result5b.func.__name__ == "F_pull", f"Expected head F_pull, got {result5b.func}"
    assert str(result5b) == "F_pull(0)"

    # ------------------------------------------------------------
    # Test 6: Inner limit that Sympy evaluates to AccumBounds(-1, 1)
    #
    #   6a) Without mixin: Limit(H(sin(1/x)), x, 0).doit() remains unevaluated.
    #   6b) With mixin:    Limit(F_pull(sin(1/x)), x, 0).doit() → F_pull(AccumBounds(-1, 1)).

    expr6a = Limit(H(sin(1/x)), x, 0)
    print(f"Test 6a (no mixin, inner unevaluated) Before .doit(): {expr6a}")
    result6a = expr6a.doit()
    print(f"Test 6a (no mixin, inner unevaluated) After  .doit(): {result6a}")
    # Since H has no _eval_limit, it stays as a Limit
    assert isinstance(result6a, type(expr6a)) and result6a == expr6a, (
        f"Expected unevaluated Limit, got {result6a}"
    )

    expr6b = Limit(F_pull(sin(1/x)), x, 0)
    print(f"Test 6b (with mixin, inner unevaluated) Before .doit(): {expr6b}")
    result6b = expr6b.doit()
    print(f"Test 6b (with mixin, inner unevaluated) After  .doit(): {result6b}")
    # Now Sympy computes lim sin(1/x) → AccumBounds(-1,1) and mixin rebuilds F_pull(...)
    assert result6b.func.__name__ == "F_pull", f"Expected head F_pull, got {result6b.func}"
    assert isinstance(result6b.args[0], AccumBounds), f"Expected an AccumBounds inside, got {result6b.args[0]}"
    assert str(result6b) == "F_pull(AccumBounds(-1, 1))"

    print("All extended limit‐mixin tests passed.")
