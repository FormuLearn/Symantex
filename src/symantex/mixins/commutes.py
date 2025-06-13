from sympy import Add, Mul, Symbol
from sympy.core.function import UndefinedFunction
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property(
    'commutes',
    "Operator is commutative in its arguments: f(a, b) = f(b, a)"
)
class CommutesFunctionMixin(PropertyMixin):
    """
    Mixin that ensures function arguments are sorted in canonical order.
    """
    @classmethod
    def eval(cls, *args):
        sorted_args = cls.sort_args(args)
        func = UndefinedFunction(cls.__name__)
        return func(*sorted_args)

@register_property(
    'commutes_add',
    "Symbol commutes under addition: x + y = y + x"
)
class CommutesAddMixin(PropertyMixin, Symbol):
    """
    Marker mixin: Sympy's Add already sorts arguments, so no override.
    """
    pass

@register_property(
    'commutes_mul',
    "Symbol commutes under multiplication: x * y = y * x"
)
class CommutesMulMixin(PropertyMixin, Symbol):
    """
    Marker mixin to enforce commutativity via Symbol(commutative=True).
    """
    def __new__(cls, name, **kwargs):
        return super().__new__(cls, name, commutative=True, **kwargs)

if __name__ == "__main__":
    from sympy import symbols
    from symantex.factory import build_operator_class, build_symbol

    print("=== Testing function-level commutes ===")
    Foo = build_operator_class('Foo', ['commutes'], 2)
    a, b = symbols('a b')
    assert Foo(a, b) == Foo(b, a)
    Bar = build_operator_class('Bar', [], 2)
    assert Bar(a, b) != Bar(b, a)
    print("Function-level tests passed.")

    print("\n=== Testing commutes_add ===")
    X = build_symbol('x', ['commutes_add'])
    Y = build_symbol('y', ['commutes_add'])
    assert X + Y == Y + X
    U, V = build_symbol('u', []), build_symbol('v', [])
    assert U + V == V + U  # default
    # non-commutative symbols
    p, q = symbols('p q', commutative=False)
    assert p*q != q*p
    print("commutes_add tests passed.")

    print("\n=== Testing commutes_mul ===")
    P = build_symbol('p', ['commutes_mul'])
    Q = build_symbol('q', ['commutes_mul'])
    assert P*Q == Q*P
    R, S = build_symbol('r', []), build_symbol('s', [])
    assert R*S == S*R  # default
    print("commutes_mul tests passed.")

    print("\n=== Testing non-commutative addition rule ===")
    # Define non_commutes_add inline
    from sympy import Add
    def NCAdd(a_, b_):
        Func = UndefinedFunction('NCAdd')
        return Func(a_, b_)
    @register_property('non_commutes_add', 'True non-commutative add')
    class NonCommAddMixin(PropertyMixin, Symbol):
        def __new__(cls, name, **kwargs):
            obj = super().__new__(cls, name, **kwargs)
            obj._property_keys = ['non_commutes_add']
            return obj
        def __add__(self, other):
            return NCAdd(self, other)
        def __radd__(self, other):
            return NCAdd(other, self)
    # Tests
    Xn = build_symbol('x', ['non_commutes_add'])
    Yn = build_symbol('y', ['non_commutes_add'])
    assert Xn + Yn != Yn + Xn
    U0, V0 = build_symbol('u0', []), build_symbol('v0', [])
    assert U0+V0 == V0+U0
    Zn, Wn = build_symbol('z', ['non_commutes_add']), build_symbol('w', [])
    assert Zn+Wn != Wn+Zn
    An, Bn = build_symbol('a', []), build_symbol('b', ['non_commutes_add'])
    assert An+Bn != Bn+An
    print("non_commutes_add tests passed.")

    print("All commutes mixin tests passed.")