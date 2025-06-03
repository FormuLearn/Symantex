from sympy import Add, Mul, Symbol, Basic
from sympy.core.function import UndefinedFunction
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property('commutes', "Operator is commutative in its arguments: f(a, b) = f(b, a)")
class CommutesFunctionMixin(PropertyMixin):
    """
    Mixin that ensures function arguments are sorted in canonical order, making the operator commutative.
    """
    def __new__(cls, *args, **kwargs):
        # Sort args using canonical Sympy ordering
        sorted_args = cls.sort_args(args)
        # Create or fetch an undefined function class for this mixin
        func = UndefinedFunction(cls.__name__)
        return func(*sorted_args)

@register_property('commutes_add', "Symbol commutes under addition: x + y = y + x")
class CommutesAddMixin(PropertyMixin, Symbol):
    """
    Mixin that ensures Symbol is commutative under addition by overriding addition.
    """
    def __new__(cls, name, **kwargs):
        # Use default Symbol constructor
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = ["commutes_add"]
        return obj

    def __add__(self, other):
        # Sort the two operands and return an Add in canonical order
        args = self.sort_args((self, other))
        return Add(args[0], args[1], evaluate=True)

    def __radd__(self, other):
        return self.__add__(other)

@register_property('commutes_mul', "Symbol commutes under multiplication: x * y = y * x")
class CommutesMulMixin(PropertyMixin, Symbol):
    """
    Mixin that ensures Symbol is commutative under multiplication by overriding multiplication.
    """
    def __new__(cls, name, **kwargs):
        # Force commutative=True so that base Symbol is treated as commutative
        obj = super().__new__(cls, name, commutative=True, **kwargs)
        obj._property_keys = ["commutes_mul"]
        return obj

    def __mul__(self, other):
        # Sort operands and return a Mul in canonical order
        from sympy import Mul as SymMul
        args = self.sort_args((self, other))
        return SymMul(args[0], args[1], evaluate=True)

    def __rmul__(self, other):
        return self.__mul__(other)

if __name__ == "__main__":
    # Tests for commutes mixins
    from symantex.factory import build_operator_class, build_symbol

    # Test function commutes
    Foo = build_operator_class('Foo', ['commutes'], arity=2)
    a_sym = Symbol('a')
    b_sym = Symbol('b')
    expr1 = Foo(a_sym, b_sym)
    expr2 = Foo(b_sym, a_sym)
    print(f"Function commute: expr1={expr1}, expr2={expr2}")
    assert expr1 == expr2

    # Test symbol addition commute
    X = build_symbol('x', ['commutes_add'])
    Y = build_symbol('y', ['commutes_add'])
    sum1 = X + Y
    sum2 = Y + X
    print(f"Symbol addition: sum1={sum1}, sum2={sum2}")
    assert sum1 == sum2

    # Test symbol multiplication commute
    U = build_symbol('u', ['commutes_mul'])
    V = build_symbol('v', ['commutes_mul'])
    prod1 = U * V
    prod2 = V * U
    print(f"Symbol multiplication: prod1={prod1}, prod2={prod2}")
    assert prod1 == prod2

    print("CommutesMixin tests passed.")
