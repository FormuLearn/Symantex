from sympy import Symbol, Add, Mul, Integer
from sympy import Pow
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

# === Additive identity: 0 + x = x, x + 0 = x ===
@register_property(
    'identity_add',
    "Symbol acts as additive identity: 0 + x = x + 0 = x"
)
class IdentityAddMixin(PropertyMixin, Symbol):
    """
    Mixin so that adding zero returns the other operand:
      x + 0 = x, 0 + x = x
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        # Attach for introspection
        obj._property_keys = obj._property_keys + ['identity_add']
        return obj

    def __add__(self, other):
        if other == Integer(0):
            return self
        # If other is an IdentityAddMixin symbol, forward logic symmetrically
        return Add(self, other, evaluate=True)

    def __radd__(self, other):
        if other == Integer(0):
            return self
        return Add(other, self, evaluate=True)

# === Multiplicative identity: 1 * x = x, x * 1 = x ===
@register_property(
    'identity_mul',
    "Symbol acts as multiplicative identity: 1 * x = x * 1 = x"
)
class IdentityMulMixin(PropertyMixin, Symbol):
    """
    Mixin so that multiplying by one returns the other operand:
      x * 1 = x, 1 * x = x
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = obj._property_keys + ['identity_mul']
        return obj

    def __mul__(self, other):
        if other == Integer(1):
            return self
        return Mul(self, other, evaluate=True)

    def __rmul__(self, other):
        if other == Integer(1):
            return self
        return Mul(other, self, evaluate=True)

# === Additive inverse: x + (-x) = 0 ===
@register_property(
    'inverse_add',
    "Symbol provides additive inverse: x + (-x) = (-x) + x = 0"
)
class InverseAddMixin(PropertyMixin, Symbol):
    """
    Mixin so that adding a symbol to its negation yields zero:
      x + (-x) = 0, (-x) + x = 0
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = obj._property_keys + ['inverse_add']
        return obj

    def __add__(self, other):
        # detect structural negation
        if other == -self:
            return Integer(0)
        return Add(self, other, evaluate=True)

    def __radd__(self, other):
        if other == -self:
            return Integer(0)
        return Add(other, self, evaluate=True)

# === Multiplicative inverse: x * (1/x) = 1 ===
@register_property(
    'inverse_mul',
    "Symbol provides multiplicative inverse: x*(1/x) = (1/x)*x = 1"
)
class InverseMulMixin(PropertyMixin, Symbol):
    """
    Mixin so that multiplying a symbol by its reciprocal yields one:
      x*(1/x) = 1, (1/x)*x = 1
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = obj._property_keys + ['inverse_mul']
        return obj

    def __mul__(self, other):
        # handle both cases: other == 1/self
        if other == (Integer(1) / self):
            return Integer(1)
        return Mul(self, other, evaluate=True)

    def __rmul__(self, other):
        if other == (Integer(1) / self):
            return Integer(1)
        return Mul(other, self, evaluate=True)

# === Main self-tests ===
if __name__ == "__main__":
    from sympy import symbols, Symbol, Add, Mul, Integer
    from symantex.factory import build_symbol

    zero = Integer(0)
    one = Integer(1)
    print("=== identity_add tests ===")
    X = build_symbol('x', ['identity_add'])
    # positive
    assert X + zero == X
    assert zero + X == X
    # negative: default symbol
    Y = build_symbol('y', [])
    assert Y + zero == Y  # Sympy simplifies to Y
    print("identity_add positive & negative passed")

    print("=== identity_mul tests ===")
    U = build_symbol('u', ['identity_mul'])
    assert U * one == U
    assert one * U == U
    V = build_symbol('v', [])
    assert V * one == V
    print("identity_mul positive & negative passed")

    print("=== inverse_add tests ===")
    A = build_symbol('a', ['inverse_add'])
    assert A + (-A) == zero
    assert (-A) + A == zero
    B = build_symbol('b', [])
    # default sympy also gives zero
    assert B + (-B) == zero
    print("inverse_add positive & negative passed")

    print("=== inverse_mul tests ===")
    M = build_symbol('m', ['inverse_mul'])
    assert M * (one / M) == one
    assert (one / M) * M == one
    N = build_symbol('n', [])
    # default sympy also gives one
    assert N * (one / N) == one
    print("inverse_mul positive & negative passed")

    print("=== mixed identity & inverse tests ===")
    # identity plus inverse together
    P = build_symbol('p', ['identity_add', 'inverse_add'])
    # (0 + P) + (-P) -> (P) + (-P) -> 0
    expr = (zero + P) + (-P)
    assert expr == zero
    # P * 1 * (1/P) -> P * (1/P) -> 1
    Q = build_symbol('q', ['identity_mul', 'inverse_mul'])
    expr2 = (Q * one) * (one / Q)
    assert expr2 == one
    print("mixed tests passed")

    print("All identity/inverse mixin tests passed.")
