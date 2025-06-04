# File: symantex/mixins/commutes.py

from sympy import Add, Symbol
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
        instance = func(*sorted_args)
        return instance


@register_property('commutes_add', "Symbol commutes under addition: x + y = y + x")
class CommutesAddMixin(PropertyMixin, Symbol):
    """
    Mixin that ensures Symbol is commutative under addition by overriding addition.
    """
    def __new__(cls, name, **kwargs):
        return super().__new__(cls, name, **kwargs)

    def __add__(self, other):
        a, b = self.sort_args((self, other))
        return Add(a, b, evaluate=True)

    def __radd__(self, other):
        return self.__add__(other)


@register_property('commutes_mul', "Symbol commutes under multiplication: x * y = y * x")
class CommutesMulMixin(PropertyMixin, Symbol):
    """
    Mixin that ensures Symbol is commutative under multiplication by overriding multiplication.
    """
    def __new__(cls, name, **kwargs):
        return super().__new__(cls, name, commutative=True, **kwargs)

    def __mul__(self, other):
        from sympy import Mul as SymMul
        a, b = self.sort_args((self, other))
        return SymMul(a, b, evaluate=True)

    def __rmul__(self, other):
        return self.__mul__(other)


if __name__ == "__main__":
    # Tests for commutes mixins
    from symantex.factory import build_operator_class, build_symbol
    from sympy import Symbol, symbols

    print("=== Testing function-level commutes ===")
    # With commutes mixin
    Foo = build_operator_class('Foo', ['commutes'], arity=2)
    a_sym = Symbol('a')
    b_sym = Symbol('b')
    expr1 = Foo(a_sym, b_sym)
    expr2 = Foo(b_sym, a_sym)
    print(f" With commutes: expr1={expr1}, expr2={expr2}")
    assert expr1 == expr2

    # Without commutes mixin
    Bar = build_operator_class('Bar', [], arity=2)
    expr3 = Bar(a_sym, b_sym)
    expr4 = Bar(b_sym, a_sym)
    print(f" Without commutes: expr3={expr3}, expr4={expr4}")
    assert expr3 != expr4

    print("\n=== Testing commutes_add ===")
    # With commutes_add only
    X = build_symbol('x', ['commutes_add'])
    Y = build_symbol('y', ['commutes_add'])
    sum1 = X + Y
    sum2 = Y + X
    print(f" With commutes_add: sum1={sum1}, sum2={sum2}")
    assert sum1 == sum2

    # Without commutes_add
    U = build_symbol('u', [])
    V = build_symbol('v', [])
    sum3 = U + V
    sum4 = V + U
    print(f" Without commutes_add: sum3={sum3}, sum4={sum4}")
    # Default Symbol is commutative under +, so these match:
    assert sum3 == sum4

    # Test non-commutativity in multiplication instead:
    a_nc, b_nc = symbols('a_nc b_nc', commutative=False)
    prod_nc1 = a_nc * b_nc
    prod_nc2 = b_nc * a_nc
    print(f" Non-commutative symbols (mul): prod_nc1={prod_nc1}, prod_nc2={prod_nc2}")
    assert prod_nc1 != prod_nc2

    print("\n=== Testing commutes_mul ===")
    # With commutes_mul only
    P = build_symbol('p', ['commutes_mul'])
    Q = build_symbol('q', ['commutes_mul'])
    prod1 = P * Q
    prod2 = Q * P
    print(f" With commutes_mul: prod1={prod1}, prod2={prod2}")
    assert prod1 == prod2

    # Without commutes_mul
    R = build_symbol('r', [])
    S = build_symbol('s', [])
    prod3 = R * S
    prod4 = S * R
    print(f" Without commutes_mul: prod3={prod3}, prod4={prod4}")
    # Default Symbol is commutative under *, so these match:
    assert prod3 == prod4

    # Test non-commutativity in multiplication explicitly:
    u_nc, v_nc = symbols('u_nc v_nc', commutative=False)
    prod_nc3 = u_nc * v_nc
    prod_nc4 = v_nc * u_nc
    print(f" Non-commutative symbols (mul): prod_nc3={prod_nc3}, prod_nc4={prod_nc4}")
    assert prod_nc3 != prod_nc4

    print("\n=== Combined tests ===")
    # commutes_add but not commutes_mul
    A = build_symbol('a', ['commutes_add'])
    B = build_symbol('b', ['commutes_add'])
    c_sum1 = A + B
    c_sum2 = B + A
    print(f" A+B with commutes_add: {c_sum1}, {c_sum2}")
    assert c_sum1 == c_sum2
    c_prod1 = A * B
    c_prod2 = B * A
    print(f" A*B without commutes_mul: {c_prod1}, {c_prod2}")
    # Again, default Symbol is commutative under *, so these match:
    assert c_prod1 == c_prod2

    # commutes_mul but not commutes_add
    M = build_symbol('m', ['commutes_mul'])
    N = build_symbol('n', ['commutes_mul'])
    d_prod1 = M * N
    d_prod2 = N * M
    print(f" M*N with commutes_mul: {d_prod1}, {d_prod2}")
    assert d_prod1 == d_prod2
    d_sum1 = M + N
    d_sum2 = N + M
    print(f" M+N without commutes_add: {d_sum1}, {d_sum2}")
    assert d_sum1 == d_sum2  # default Symbol is commutative under +

    print("\nAll CommutesMixin tests passed.")
