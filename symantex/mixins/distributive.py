from sympy import Add, Mul, Symbol, symbols
from sympy.core.function import UndefinedFunction
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property(
    'commutes',
    "Operator is commutative in its arguments: f(a, b) = f(b, a)"
)
class CommutesFunctionMixin(PropertyMixin):
    """
    Mixin that ensures function arguments are sorted in canonical order, making the operator commutative.
    """
    @classmethod
    def eval(cls, *args):
        # Sort args using canonical Sympy ordering
        sorted_args = cls.sort_args(args)
        # Construct the function via UndefinedFunction to preserve dynamic class name
        func = UndefinedFunction(cls.__name__)
        return func(*sorted_args)

@register_property(
    'commutes_add',
    "Symbol commutes under addition: x + y = y + x"
)
class CommutesAddMixin(PropertyMixin, Symbol):
    """
    Marker mixin to mark a Symbol as "commutes under +".  Sympy's Add already
    sorts arguments, so no override is strictly necessary.
    """
    pass

@register_property(
    'commutes_mul',
    "Symbol commutes under multiplication: x * y = y * x"
)
class CommutesMulMixin(PropertyMixin, Symbol):
    """
    Marker mixin to mark a Symbol as "commutes under *".  Sympy's Mul already
    sorts arguments, so no override is strictly necessary.
    """
    def __new__(cls, name, **kwargs):
        # Ensure symbol is declared commutative
        return super().__new__(cls, name, commutative=True, **kwargs)

@register_property(
    'non_commutes_add',
    "Symbol uses a truly non-commutative addition: x + y -> NCAdd(x, y)"
)
class NonCommAddMixin(PropertyMixin, Symbol):
    """
    Mixin that replaces x + y with NCAdd(x, y), a non-commutative addition node.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = ['non_commutes_add']
        return obj

    def __add__(self, other):
        return NCAdd(self, other)

    def __radd__(self, other):
        return NCAdd(other, self)


def NCAdd(a, b):
    """
    Create a non-commutative "addition" node NCAdd(a, b).  Never reorders args.
    """
    Func = UndefinedFunction("NCAdd")
    return Func(a, b)


if __name__ == "__main__":
    from symantex.factory import build_operator_class, build_symbol
    from sympy import Symbol, Add, Mul, symbols

    a_sym, b_sym = Symbol('a'), Symbol('b')
    # === Function-level commutes ===
    print("=== Testing function-level commutes ===")
    Foo = build_operator_class('Foo', ['commutes'], arity=2)
    expr1 = Foo(a_sym, b_sym)
    expr2 = Foo(b_sym, a_sym)
    print(f" With commutes: Foo(a,b)={expr1}, Foo(b,a)={expr2}")
    assert expr1 == expr2

    Bar = build_operator_class('Bar', [], arity=2)
    expr3 = Bar(a_sym, b_sym)
    expr4 = Bar(b_sym, a_sym)
    print(f" Without commutes: Bar(a,b)={expr3}, Bar(b,a)={expr4}")
    assert expr3 != expr4
    print("Function-level commutes tests passed.\n")

    # === Symbol-level commutes_add ===
    print("=== Testing commutes_add ===")
    X = build_symbol('x', ['commutes_add'])
    Y = build_symbol('y', ['commutes_add'])
    sum1 = X + Y
    sum2 = Y + X
    print(f" With commutes_add: x+y={sum1}, y+x={sum2}")
    assert sum1 == sum2

    # Negative: marker only, but default symbols also commute under +
    U, V = build_symbol('u', []), build_symbol('v', [])
    sum3, sum4 = U + V, V + U
    print(f" Without commutes_add: u+v={sum3}, v+u={sum4}")
    assert sum3 == sum4
    # Ensure no property key on Add
    assert getattr((sum3).func, 'property_keys', None) is None
    print("Symbol-level commutes_add tests passed.\n")

    # === Symbol-level commutes_mul ===
    print("=== Testing commutes_mul ===")
    P = build_symbol('p', ['commutes_mul'])
    Q = build_symbol('q', ['commutes_mul'])
    prod1, prod2 = P * Q, Q * P
    print(f" With commutes_mul: p*q={prod1}, q*p={prod2}")
    assert prod1 == prod2

    # Negative: default symbols (commutative True) also match, but no key
    R, S = build_symbol('r', []), build_symbol('s', [])
    prod3, prod4 = R * S, S * R
    print(f" Without commutes_mul: r*s={prod3}, s*r={prod4}")
    assert prod3 == prod4
    assert getattr((prod3).func, 'property_keys', None) is None
    print("Symbol-level commutes_mul tests passed.\n")

    # === Non-commutative addition ===
    print("=== Testing non_commutes_add ===")
    Xn = build_symbol('x', ['non_commutes_add'])
    Yn = build_symbol('y', ['non_commutes_add'])
    expr_nc1 = Xn + Yn
    expr_nc2 = Yn + Xn
    print(f" With non_commutes_add both: x+y={expr_nc1}, y+x={expr_nc2}")
    assert expr_nc1 != expr_nc2
    assert expr_nc1.func.__name__ == 'NCAdd' and expr_nc1.args == (Xn, Yn)
    assert expr_nc2.args == (Yn, Xn)

    # Negative: neither has mixin
    U0, V0 = build_symbol('u0', []), build_symbol('v0', [])
    nsum1, nsum2 = U0 + V0, V0 + U0
    print(f" Without non_commutes_add: u0+v0={nsum1}, v0+u0={nsum2}")
    assert nsum1 == nsum2 and isinstance(nsum1, Add)

    # Left-only
    Z = build_symbol('z', ['non_commutes_add'])
    W = build_symbol('w', [])
    mix1, mix2 = Z + W, W + Z
    print(f" Left-only mixin: z+w={mix1}, w+z={mix2}")
    assert mix1.func.__name__ == 'NCAdd' and isinstance(mix2, Add)

    # Right-only
    A, B = build_symbol('a', []), build_symbol('b', ['non_commutes_add'])
    mix3, mix4 = A + B, B + A
    print(f" Right-only mixin: a+b={mix3}, b+a={mix4}")
    assert isinstance(mix3, Add) and mix4.func.__name__ == 'NCAdd'
    print("Non-commutative addition tests passed.\n")

    print("All CommutesMixin tests passed (positive & negative).")
