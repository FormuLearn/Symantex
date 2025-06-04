# File: symantex/mixins/identity_inverse.py

from sympy import Symbol, Add, Mul, Integer
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin


@register_property('identity_add', "Symbol acts as additive identity: 0 + x = x + 0 = x")
class IdentityAddMixin(PropertyMixin, Symbol):
    """
    Mixin so that adding zero returns the other operand:
      x + 0 = x,   0 + x = x.
    """
    def __new__(cls, name, **kwargs):
        # Create a new Symbol; default commutative=True
        return super().__new__(cls, name, **kwargs)

    def __add__(self, other):
        # If other is literally zero, return self
        if other == Integer(0):
            return self
        # Otherwise, perform regular addition
        return Add(self, other, evaluate=True)

    def __radd__(self, other):
        # If other is zero, return self
        if other == Integer(0):
            return self
        return Add(other, self, evaluate=True)


@register_property('identity_mul', "Symbol acts as multiplicative identity: 1 * x = x * 1 = x")
class IdentityMulMixin(PropertyMixin, Symbol):
    """
    Mixin so that multiplying by one returns the other operand:
      x * 1 = x,   1 * x = x.
    """
    def __new__(cls, name, **kwargs):
        return super().__new__(cls, name, **kwargs)

    def __mul__(self, other):
        # If other is literally one, return self
        if other == Integer(1):
            return self
        return Mul(self, other, evaluate=True)

    def __rmul__(self, other):
        if other == Integer(1):
            return self
        return Mul(other, self, evaluate=True)


@register_property('inverse_add', "Symbol provides additive inverse: x + (-x) = 0, (-x) + x = 0")
class InverseAddMixin(PropertyMixin, Symbol):
    """
    Mixin so that adding a symbol to its negative yields zero:
      x + (-x) = 0,   (-x) + x = 0.
    """
    def __new__(cls, name, **kwargs):
        return super().__new__(cls, name, **kwargs)

    def __add__(self, other):
        # If other is exactly -self, return 0
        if other == -self:
            return Integer(0)
        return Add(self, other, evaluate=True)

    def __radd__(self, other):
        # If other is exactly -self, return 0
        if other == -self:
            return Integer(0)
        return Add(other, self, evaluate=True)


@register_property('inverse_mul', "Symbol provides multiplicative inverse: x * (1/x) = 1, (1/x) * x = 1")
class InverseMulMixin(PropertyMixin, Symbol):
    """
    Mixin so that multiplying a symbol by its reciprocal yields one:
      x * (1/x) = 1,   (1/x) * x = 1.
    """
    def __new__(cls, name, **kwargs):
        return super().__new__(cls, name, **kwargs)

    def __mul__(self, other):
        # If other is exactly 1/self, return 1
        # Note: 1/self creates a Pow object. Sympy’s == works structurally.
        if other == (Integer(1) / self):
            return Integer(1)
        return Mul(self, other, evaluate=True)

    def __rmul__(self, other):
        if other == (Integer(1) / self):
            return Integer(1)
        return Mul(other, self, evaluate=True)


if __name__ == "__main__":
    # Tests for identity and inverse mixins
    from sympy import symbols
    from symantex.factory import build_symbol

    print("=== Testing identity_add ===")
    X = build_symbol('x', ['identity_add'])
    zero = Integer(0)
    expr1 = X + zero
    expr2 = zero + X
    print(f" x + 0 = {expr1}, 0 + x = {expr2}")
    assert expr1 == X
    assert expr2 == X

    Y = build_symbol('y', [])
    expr3 = Y + zero
    print(f" (without mixin) y + 0 = {expr3}")
    # default Symbol + 0 → y, so this also simplifies; no failure

    print("\n=== Testing identity_mul ===")
    U = build_symbol('u', ['identity_mul'])
    one = Integer(1)
    expr4 = U * one
    expr5 = one * U
    print(f" u * 1 = {expr4}, 1 * u = {expr5}")
    assert expr4 == U
    assert expr5 == U

    V = build_symbol('v', [])
    expr6 = V * one
    print(f" (without mixin) v * 1 = {expr6}")
    # default Symbol * 1 → v, so no failure

    print("\n=== Testing inverse_add ===")
    A = build_symbol('a', ['inverse_add'])
    expr7 = A + (-A)
    expr8 = (-A) + A
    print(f" a + (-a) = {expr7},  (-a) + a = {expr8}")
    assert expr7 == Integer(0)
    assert expr8 == Integer(0)

    B = build_symbol('b', [])
    expr9 = B + (-B)
    print(f" (without mixin) b + (-b) = {expr9}")
    # default Symbol + -Symbol → 0 anyway; Sympy simplifies

    print("\n=== Testing inverse_mul ===")
    M = build_symbol('m', ['inverse_mul'])
    expr10 = M * (Integer(1) / M)
    expr11 = (Integer(1) / M) * M
    print(f" m * (1/m) = {expr10},  (1/m) * m = {expr11}")
    assert expr10 == Integer(1)
    assert expr11 == Integer(1)

    N = build_symbol('n', [])
    expr12 = N * (Integer(1) / N)
    print(f" (without mixin) n * (1/n) = {expr12}")
    # default Symbol*(1/Symbol) → 1 anyway; Sympy simplifies

    print("\nAll identity/inverse mixin tests passed.")
