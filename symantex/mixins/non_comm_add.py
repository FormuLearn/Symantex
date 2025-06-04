# File: symantex/mixins/non_comm_add.py

from sympy import Symbol
from sympy.core.function import UndefinedFunction
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin


def NCAdd(a, b):
    """
    Create a non-commutative “addition” node NCAdd(a, b).  This never reorders its arguments.
    """
    Func = UndefinedFunction("NCAdd")
    return Func(a, b)


@register_property(
    'non_commutes_add',
    "Symbol uses a truly non-commutative addition: x + y → NCAdd(x, y)"
)
class NonCommAddMixin(PropertyMixin, Symbol):
    """
    Mixin that replaces the usual `x + y` → `Add(x, y)` with `NCAdd(x, y)`.
    As a result, NCAdd(x, y) ≠ NCAdd(y, x).
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = ["non_commutes_add"]
        return obj

    def __add__(self, other):
        # If this symbol has the mixin, always use NCAdd(self, other)
        return NCAdd(self, other)

    def __radd__(self, other):
        # If other is a plain Symbol, W + Z will call Z.__radd__, but Python
        # first tries W.__add__(Z) → plain Add(W, Z).  __radd__ only runs if
        # W.__add__ fails.  Therefore, in practice, W + Z uses Add(W, Z),
        # not NCAdd(W, Z).  That is expected.
        return NCAdd(other, self)


if __name__ == "__main__":
    # Tests for NonCommAddMixin
    from symantex.factory import build_symbol
    from sympy import Symbol, Add

    print("=== Testing NonCommAddMixin ===")

    # 1) Both symbols carry the mixin
    X = build_symbol('x', ['non_commutes_add'])
    Y = build_symbol('y', ['non_commutes_add'])
    expr1 = X + Y
    expr2 = Y + X
    print(f" With mixin on both: X+Y = {expr1}, Y+X = {expr2}")
    assert expr1 != expr2, "Expected NCAdd(x, y) ≠ NCAdd(y, x)"
    # Check head and args
    print(f"  Head of X+Y: {expr1.func}, args: {expr1.args}")
    assert expr1.func.__name__ == "NCAdd"
    assert expr1.args == (X, Y)
    assert expr2.args == (Y, X)

    # 2) Neither symbol carries the mixin
    U = build_symbol('u', [])
    V = build_symbol('v', [])
    sum1 = U + V    # → Add(u, v)
    sum2 = V + U    # → Add(u, v)
    print(f" Without mixin: U+V = {sum1}, V+U = {sum2}")
    assert sum1 == sum2, "Default Symbol addition is commutative (Add)."
    assert isinstance(sum1, Add)

    # 3) Left operand has mixin, right does not
    Z = build_symbol('z', ['non_commutes_add'])
    W = build_symbol('w', [])
    mix1 = Z + W    # Z has mixin → NCAdd(z, w)
    mix2 = W + Z    # W is plain → W.__add__(Z) = Add(w, z)
    print(f" Left‐mixin only: Z+W = {mix1}, W+Z = {mix2}")
    assert mix1.func.__name__ == "NCAdd"
    assert mix1.args == (Z, W)
    # We expect mix2 to be a plain Add, not NCAdd
    assert isinstance(mix2, Add)

    # 4) Right operand has mixin, left does not
    A = build_symbol('a', [])
    B = build_symbol('b', ['non_commutes_add'])
    mix3 = A + B     # A is plain → Add(a, b)
    mix4 = B + A     # B has mixin → NCAdd(b, a)
    print(f" Right‐mixin only: A+B = {mix3}, B+A = {mix4}")
    assert isinstance(mix3, Add)
    assert mix4.func.__name__ == "NCAdd"
    assert mix4.args == (B, A)

    print("\nAll NonCommAddMixin tests passed.")
