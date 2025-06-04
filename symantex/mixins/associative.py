# File: symantex/mixins/associative.py

from sympy import Add, Mul, Symbol
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin


@register_property('associative', "Operator is associative: f(f(a, b), c) = f(a, f(b, c))")
class AssociativeMixin(PropertyMixin):
    """
    Mixin that enforces right‐associative grouping for a binary operator.
    If the first argument is already an instance of this same operator, re‐associate.

    In other words:
      f(f(a,b), c)  →  f(a, f(b,c))
    """
    def __new__(cls, *args, **kwargs):
        # Expect exactly two arguments for a binary operator
        if len(args) == 2:
            a, b = args
            # If `a` is already an instance of this operator, re‐associate:
            # f(f(a0,a1), b) → f(a0, f(a1, b))
            if isinstance(a, cls):
                inner_left, inner_right = a.args
                # Recurse to ensure full right‐association
                return cls(inner_left, cls(inner_right, b))
        # Otherwise, let Sympy create an instance of "cls" itself:
        instance = super().__new__(cls, *args, **kwargs)
        instance._property_keys = ["associative"]
        return instance


@register_property('associative_add', "Symbol addition is associative: (x + y) + z = x + (y + z)")
class AssociativeAddMixin(PropertyMixin, Symbol):
    """
    Mixin to mark a Symbol as “associative under +.”  Since Sympy’s built‐in Add is already
    associative (it automatically flattens nested addition), we simply attach the property key.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, **kwargs)
        obj._property_keys = ['associative_add']
        return obj
    # No need to override __add__; Sympy’s Add is natively associative.


@register_property('associative_mul', "Symbol multiplication is associative: (x * y) * z = x * (y * z)")
class AssociativeMulMixin(PropertyMixin, Symbol):
    """
    Mixin to mark a Symbol as “associative under *.”  Since Sympy’s built‐in Mul is already
    associative (it automatically flattens nested multiplication), we simply attach the property key.
    """
    def __new__(cls, name, **kwargs):
        obj = super().__new__(cls, name, commutative=True, **kwargs)
        obj._property_keys = ['associative_mul']
        return obj
    # No need to override __mul__; Sympy’s Mul is natively associative.


if __name__ == "__main__":
    from symantex.factory import build_symbol, build_operator_class
    from sympy import Symbol, Add, Mul

    print("=== Testing Function‐level associativity ===")
    Foo = build_operator_class('Foo', ['associative'], arity=2)

    a_sym = Symbol('a')
    b_sym = Symbol('b')
    c_sym = Symbol('c')

    # Build using left‐nested grouping.  Our mixin should immediately convert it to right‐nested.
    expr_left  = Foo(Foo(a_sym, b_sym), c_sym)
    expr_right = Foo(a_sym, Foo(b_sym, c_sym))

    print(f" Before grouping:  Foo(Foo(a,b), c) = {expr_left}")
    print(f" Re‐associated:     Foo(a, Foo(b,c)) = {expr_right}")
    assert expr_left == expr_right, "Function‐level associativity failed (semantic)."

    # Check AST shape: ensure it is actually right‐nested.
    print(" AST of re‐associated expression:", expr_right, "→ args:", expr_right.args)
    left_part, right_part = expr_right.args
    assert left_part == a_sym
    assert right_part.func.__name__ == "Foo" and right_part.args == (b_sym, c_sym)

    print("Function‐level associative mixin test passed.\n")

    print("=== Testing Symbol‐level associativity for addition ===")
    X = build_symbol('x', ['associative_add'])
    Y = build_symbol('y', ['associative_add'])
    Z = build_symbol('z', ['associative_add'])

    # Sympy’s Add flattens, so both groupings give the same internal tuple of args:
    sum_left  = Add(Add(X, Y), Z)   # ((x + y) + z)
    sum_right = Add(X, Add(Y, Z))   # (x + (y + z))

    print(f" (x + y) + z = {sum_left}")
    print(f" x + (y + z) = {sum_right}")
    assert sum_left == sum_right, "Symbol addition should be equal under associativity."
    print(" AST args for both additions:", sum_left.args, sum_right.args)
    assert sum_left.args == sum_right.args == (X, Y, Z)

    print("Symbol‐level associative_add test passed.\n")

    print("=== Testing Symbol‐level associativity for multiplication ===")
    U = build_symbol('u', ['associative_mul'])
    V = build_symbol('v', ['associative_mul'])
    W = build_symbol('w', ['associative_mul'])

    prod_left  = Mul(Mul(U, V), W)   # ((u * v) * w)
    prod_right = Mul(U, Mul(V, W))   # (u * (v * w))

    print(f" (u * v) * w = {prod_left}")
    print(f" u * (v * w) = {prod_right}")
    assert prod_left == prod_right, "Symbol multiplication should be equal under associativity."
    print(" AST args for both multiplications:", prod_left.args, prod_right.args)
    assert prod_left.args == prod_right.args == (U, V, W)

    print("Symbol‐level associative_mul test passed.\n")

    print("All AssociativeMixin tests passed.")
