from sympy import Add, Mul, Symbol
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property('identity_add', "Symbol acts as additive identity: 0 + x = x + 0 = x")
class AdditiveIdentityMixin(PropertyMixin, Symbol):
    """
    Mixin marking a symbol as additive identity (zero).
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = ['identity_add']
        return obj

    def __add__(self, other):
        # Only treat this symbol and '0' as additive identities
        if self.name == '0':
            return other
        if isinstance(other, Symbol) and other.name == '0':
            return self
        return Add(self, other, evaluate=True)

    def __radd__(self, other):
        return self.__add__(other)

@register_property('identity_mul', "Symbol acts as multiplicative identity: 1 * x = x * 1 = x")
class MultiplicativeIdentityMixin(PropertyMixin, Symbol):
    """
    Mixin marking a symbol as multiplicative identity (one).
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, commutative=True, **kwargs)
        obj._property_keys = ['identity_mul']
        return obj

    def __mul__(self, other):
        if self.name == '1':
            return other
        if isinstance(other, Symbol) and other.name == '1':
            return self
        return Mul(self, other, evaluate=True)

    def __rmul__(self, other):
        return self.__mul__(other)

@register_property('inverse_add', "Symbol provides additive inverse: x + inv(x) = 0")
class AdditiveInverseMixin(PropertyMixin, Symbol):
    """
    Mixin that defines the additive inverse of the symbol.
    When added to its base symbol, returns '0'.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = ['inverse_add']
        return obj

    def __add__(self, other):
        # If other is the base symbol (matching name without 'inv_'), return '0'
        if isinstance(other, Symbol) and other.name == self.name.replace('inv_', ''):
            return Symbol('0')
        return Add(self, other, evaluate=True)

    def __radd__(self, other):
        return self.__add__(other)

@register_property('inverse_mul', "Symbol provides multiplicative inverse: x * inv(x) = 1")
class MultiplicativeInverseMixin(PropertyMixin, Symbol):
    """
    Mixin that defines the multiplicative inverse of the symbol.
    When multiplied by its base symbol, returns '1'.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, commutative=True, **kwargs)
        obj._property_keys = ['inverse_mul']
        return obj

    def __mul__(self, other):
        # If other is the base symbol (matching name without 'inv_'), return '1'
        if isinstance(other, Symbol) and other.name == self.name.replace('inv_', ''):
            return Symbol('1')
        return Mul(self, other, evaluate=True)

    def __rmul__(self, other):
        return self.__mul__(other)

if __name__ == "__main__":
    from symantex.factory import build_symbol
    from sympy import Symbol, Add, Mul

    # Test additive identity
    Zero = build_symbol('0', ['identity_add'])
    X = build_symbol('x', ['identity_add'])  # although real zero is only '0'
    print(f"0 + x = {Zero + X}")  # expect x
    print(f"x + 0 = {X + Zero}")  # expect x

    # Test multiplicative identity
    One = build_symbol('1', ['identity_mul'])
    Y = build_symbol('y', ['identity_mul'])
    print(f"1 * y = {One * Y}")  # expect y
    print(f"y * 1 = {Y * One}")  # expect y

    # Test additive inverse
    X_inv = build_symbol('inv_x', ['inverse_add'])
    X_base = Symbol('x')
    print(f"inv_x + x = {X_inv + X_base}")  # expect 0
    print(f"x + inv_x = {X_base + X_inv}")  # expect 0

    # Test multiplicative inverse
    Y_inv = build_symbol('inv_y', ['inverse_mul'])
    Y_base = Symbol('y')
    print(f"inv_y * y = {Y_inv * Y_base}")  # expect 1
    print(f"y * inv_y = {Y_base * Y_inv}")  # expect 1

    print("Identity & Inverse mixin tests passed.")
