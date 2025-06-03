from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin
from sympy import Symbol

@register_property('distribute_mul_add', "Symbol multiplication distributes over addition: x*(y+z) = x*y + x*z")
class DistributeMulAddMixin(PropertyMixin, Symbol):
    """
    Mixin that ensures Symbol multiplication distributes over addition.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, commutative=True, **kwargs)
        obj._property_keys = ['distribute_mul_add']
        return obj

    def __mul__(self, other):
        from sympy import Add, Mul as SymMul
        if isinstance(other, Add):
            return Add(*[SymMul(self, term, evaluate=True) for term in other.args], evaluate=True)
        return SymMul(self, other, evaluate=True)

    def __rmul__(self, other):
        from sympy import Add, Mul as SymMul
        if isinstance(other, Add):
            return Add(*[SymMul(term, self, evaluate=True) for term in other.args], evaluate=True)
        return self.__mul__(other)
    

if __name__ == "__main__":
    from symantex.factory import build_symbol
    from symantex.mixins.commutes import CommutesAddMixin # so it's registered

    X = build_symbol('x', ['commutes_add'])

    D = build_symbol('d', ['distribute_mul_add'])
    E = build_symbol('e', ['distribute_mul_add'])
    F = build_symbol('f', ['distribute_mul_add'])
    expr_dist = D * (E + X)
    expected_dist = D * E + D * X
    assert expr_dist == expected_dist

    print("All algebraic property mixin tests passed.")