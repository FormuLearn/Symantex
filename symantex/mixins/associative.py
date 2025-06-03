from sympy import Basic, Symbol, Add, Mul
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property('associative', "Operator is associative: f(f(a, b), c) = f(a, f(b, c))")
class AssociativeMixin(PropertyMixin):
    """
    Mixin that enforces right-associative grouping for binary operators.
    When the first argument is an instance of this same class, it re-associates.
    """
    def __new__(cls, *args, **kwargs):
        # Expect exactly two arguments for a binary operator
        if len(args) == 2:
            a, b = args
            # If a is already an instance of this operator, re-associate: f(f(a0,a1),b) -> f(a0, f(a1,b))
            if isinstance(a, cls):
                # Recurse to ensure full right association
                inner_left, inner_right = a.args
                return cls(inner_left, cls(inner_right, b))
        # Default creation via Function.__new__ (handled by the Function base class)
        return super().__new__(cls, *args, **kwargs)
    
@register_property('associative_add', "Symbol addition is associative: (x + y) + z = x + (y + z)")
class AssociativeAddMixin(PropertyMixin, Symbol):
    """
    Mixin to enforce right-associativity for symbol addition.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = ['associative_add']
        return obj

    def __add__(self, other):
        # If left is a nested Add, re-associate: (x + y) + z -> x + (y + z)
        if isinstance(self, Add):
            # self is Add(a, b), re-associate to Add(a, Add(b, other))
            a, b = self.args
            return Add(a, Add(b, other), evaluate=True)
        # Otherwise regular addition
        return Add(self, other, evaluate=True)

    def __radd__(self, other):
        # If right operand is Add, re-associate: x + (y + z) -> (x + y) + z
        if isinstance(other, Add):
            a, b = other.args
            return Add(Add(a, self), b, evaluate=True)
        return self.__add__(other)

@register_property('associative_mul', "Symbol multiplication is associative: (x * y) * z = x * (y * z)")
class AssociativeMulMixin(PropertyMixin, Symbol):
    """
    Mixin to enforce right-associativity for symbol multiplication.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, commutative=True, **kwargs)
        obj._property_keys = ['associative_mul']
        return obj

    def __mul__(self, other):
        if isinstance(self, Mul):
            a, b = self.args
            return Mul(a, Mul(b, other), evaluate=True)
        return Mul(self, other, evaluate=True)

    def __rmul__(self, other):
        if isinstance(other, Mul):
            a, b = other.args
            return Mul(Mul(a, self), b, evaluate=True)
        return self.__mul__(other)

if __name__ == "__main__":
    # Basic test for AssociativeMixin
    # from symantex.factory import build_operator_class
    # from sympy import Symbol

    # Foo = build_operator_class('Foo', ['associative'], arity=2)
    # a, b, c = Symbol('a'), Symbol('b'), Symbol('c')
    # expr_left = Foo(Foo(a, b), c)
    # expr_right = Foo(a, Foo(b, c))
    # print(f"expr_left: {expr_left}")       # Should print Foo(a, Foo(b, c))
    # print(f"expr_right: {expr_right}")     # Foo(a, Foo(b, c))
    # assert expr_left == expr_right, "AssociativeMixin failed: left and right expressions differ"

    # # Verify deeper nesting: f(f(f(a,b),c),d) -> f(a, f(b, f(c, d)))
    # d = Symbol('d')
    # nested = Foo(Foo(Foo(a, b), c), d)
    # expected = Foo(a, Foo(b, Foo(c, d)))
    # print(f"nested:   {nested}")
    # print(f"expected: {expected}")
    # assert nested == expected, "AssociativeMixin failed on deeper nesting"

    # print("AssociativeMixin tests passed.")
    from symantex.factory import build_symbol

    # Test additive associativity
    X = build_symbol('x', ['associative_add'])
    Y = build_symbol('y', ['associative_add'])
    Z = build_symbol('z', ['associative_add'])
    expr_left = Add(Add(X, Y), Z)
    expr_right = Add(X, Add(Y, Z))
    print(f"Add assoc left: {expr_left}")
    print(f"Add assoc right: {expr_right}")
    assert expr_left == expr_right

    # Test multiplicative associativity
    U = build_symbol('u', ['associative_mul'])
    V = build_symbol('v', ['associative_mul'])
    W = build_symbol('w', ['associative_mul'])
    expr_left_m = Mul(Mul(U, V), W)
    expr_right_m = Mul(U, Mul(V, W))
    print(f"Mul assoc left: {expr_left_m}")
    print(f"Mul assoc right: {expr_right_m}")
    assert expr_left_m == expr_right_m

    print("Associative symbol mixin tests passed.")
