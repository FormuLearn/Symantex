# File: symantex/mixins/distributive.py

from sympy import Symbol, Add
from symantex.registry import register_property, store_original_method
from symantex.mixins.base import PropertyMixin


# ────────────────────────────────────────────────────────────────────────────────
# 1) “Left‐distribution” mixin
# ────────────────────────────────────────────────────────────────────────────────

@register_property(
    'distribute_mul_add_left',
    "Symbol multiplication distributes over addition on the left: x*(y+z) = x*y + x*z"
)
class DistributeMulAddLeftMixin(PropertyMixin, Symbol):
    def __new__(cls, name, **kwargs):
        # Create a new Symbol (Symbol defaults to commutative=True)
        return super().__new__(cls, name, **kwargs)

    def __mul__(self, other):
        # If the right‐hand side is an Add, distribute over its args
        if isinstance(other, Add):
            from sympy import Mul as SymMul
            return Add(
                *[SymMul(self, term, evaluate=True) for term in other.args],
                evaluate=True
            )
        # Otherwise, behave exactly like normal Mul
        from sympy import Mul as SymMul
        return SymMul(self, other, evaluate=True)

    def __rmul__(self, other):
        # If the left‐hand side is an Add, distribute on the right as well
        if isinstance(other, Add):
            from sympy import Mul as SymMul
            return Add(
                *[SymMul(term, self, evaluate=True) for term in other.args],
                evaluate=True
            )
        # Otherwise, fallback to Symbol.__rmul__
        return super().__rmul__(other)


# ────────────────────────────────────────────────────────────────────────────────
# 2) “Right‐distribution” mixin (patches Add.__mul__)
# ────────────────────────────────────────────────────────────────────────────────

@register_property(
    'distribute_mul_add_right',
    "Distribute addition over multiplication on the right: (y+z)*x = y*x + z*x"
)
class DistributeMulAddRightMixin(PropertyMixin, Symbol):
    """
    Mixin that patches sympy.Add.__mul__ so that, when you do (Y+Z)*X,
    if X._property_keys contains "distribute_mul_add_right", then Add.__mul__
    delegates to X.__rmul__, forcing the expansion.

    We implement this by overriding __init_subclass__ (invoked at class‐creation time)
    to perform exactly one global patch of Add.__mul__.  We also store the original
    Add.__mul__ so that get_original_method("distribute_mul_add_right") works.
    """

    def __new__(cls, name, **kwargs):
        # Create a new Symbol (Symbol defaults to commutative=True)
        return super().__new__(cls, name, **kwargs)

    def __rmul__(self, other):
        # This is invoked when something like Add(...) * self happens after patch.
        # To distribute, if other is Add, expand over its args.
        if isinstance(other, Add):
            from sympy import Mul as SymMul
            return Add(
                *[SymMul(term, self, evaluate=True) for term in other.args],
                evaluate=True
            )
        # Otherwise, default behavior
        return super().__rmul__(other)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Only patch Add.__mul__ once
        if getattr(Add, "_patched_for_distribute_right", False):
            return
        Add._patched_for_distribute_right = True

        # Save the original Add.__mul__
        original_add_mul = Add.__mul__
        store_original_method('distribute_mul_add_right', original_add_mul)

        def patched_add_mul(self, other):
            """
            When Add.__mul__(self, other) is called, inspect other._property_keys.
            If it contains "distribute_mul_add_right", delegate to other.__rmul__(self).
            Otherwise, fall back to the original Add.__mul__.
            """
            prop_keys = getattr(other, "_property_keys", [])
            if "distribute_mul_add_right" in prop_keys:
                return other.__rmul__(self)
            return original_add_mul(self, other)

        Add.__mul__ = patched_add_mul


# ────────────────────────────────────────────────────────────────────────────────
# 3) Tests (run via `python distributive.py`)
# ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from sympy import symbols
    from symantex.factory import build_symbol

    print("=== Testing distribute_mul_add mixins ===")

    # ─── (a) Left‐distribution ONLY ───────────────────────────────────────────────
    D1 = build_symbol('d1', ['distribute_mul_add_left'])
    E1 = build_symbol('e1', [])
    X1 = build_symbol('x1', [])

    expr1 = D1 * (E1 + X1)
    expected1 = D1*E1 + D1*X1
    print(f" Left only: {D1}*({E1}+{X1}) = {expr1}  (expected {expected1})")
    assert expr1 == expected1

    expr1b = (E1 + X1) * D1
    print(f" Left only: ({E1}+{X1})*{D1} = {expr1b}  (no distribution on right)")
    assert expr1b == (E1 + X1)*D1

    # ─── (b) Right‐distribution ONLY ──────────────────────────────────────────────
    D2 = build_symbol('d2', ['distribute_mul_add_right'])
    E2 = build_symbol('e2', [])
    X2 = build_symbol('x2', [])

    expr2 = D2 * (E2 + X2)
    print(f" Right only: {D2}*({E2}+{X2}) = {expr2}  (no left‐distribution)")
    assert expr2 == D2*(E2 + X2)

    expr2b = (E2 + X2) * D2
    expected2b = E2*D2 + X2*D2
    print(f" Right only: ({E2}+{X2})*{D2} = {expr2b}  (expected {expected2b})")
    assert expr2b == expected2b

    # ─── (c) BOTH left and right ──────────────────────────────────────────────────
    D3 = build_symbol('d3', ['distribute_mul_add_left', 'distribute_mul_add_right'])
    E3 = build_symbol('e3', [])
    X3 = build_symbol('x3', [])

    expr3 = D3 * (E3 + X3)
    expected3 = D3*E3 + D3*X3
    print(f" Both sides: {D3}*({E3}+{X3}) = {expr3}  (expected {expected3})")
    assert expr3 == expected3

    expr3b = (E3 + X3) * D3
    expected3b = E3*D3 + X3*D3
    print(f" Both sides: ({E3}+{X3})*{D3} = {expr3b}  (expected {expected3b})")
    assert expr3b == expected3b

    # ─── (d) NEITHER left nor right ───────────────────────────────────────────────
    D4 = build_symbol('d4', [])  # no distribution keys
    E4 = build_symbol('e4', [])
    X4 = build_symbol('x4', [])

    expr4a = D4 * (E4 + X4)
    expr4b = (E4 + X4) * D4
    print(f" Neither: {D4}*({E4}+{X4}) = {expr4a}  (should remain Mul)")
    print(f" Neither: ({E4}+{X4})*{D4} = {expr4b}  (should remain Mul)")
    assert expr4a == D4*(E4 + X4)
    assert expr4b == (E4 + X4)*D4

    print("\nAll distribute_mul_add mixin tests passed.")