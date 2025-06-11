from sympy import Add, Mul, Symbol
from symantex.registry import register_property
from symantex.mixins.base import PropertyMixin

@register_property(
    'associative',
    "Operator is associative: f(f(a, b), c) = f(a, f(b, c))"
)
class AssociativeMixin(PropertyMixin):
    """
    Mixin that enforces right‐associative grouping for a binary operator.
    If the first argument is already an instance of this same operator, re‐associate.

    In other words:
      f(f(a, b), c)  →  f(a, f(b, c))
    """
    @classmethod
    def eval(cls, *args):
        # Only handle the binary case where the first argument is the same operator
        if len(args) == 2 and isinstance(args[0], cls):
            inner_left, inner_right = args[0].args
            # Recurse to enforce full right‐association
            return cls(inner_left, cls(inner_right, args[1]))
        return None

@register_property(
    'associative_add',
    "Symbol addition is associative: (x + y) + z = x + (y + z)"
)
class AssociativeAddMixin(PropertyMixin):
    """
    Marker mixin to mark a Symbol as “associative under +.”
    Sympy’s Add already flattens nested addition, so no behavior is needed.
    """
    pass

@register_property(
    'associative_mul',
    "Symbol multiplication is associative: (x * y) * z = x * (y * z)"
)
class AssociativeMulMixin(PropertyMixin):
    """
    Marker mixin to mark a Symbol as “associative under *.”
    Sympy’s Mul already flattens nested multiplication, so no behavior is needed.
    """
    pass

if __name__ == "__main__":
    from symantex.factory import build_symbol, build_operator_class
    from sympy import Symbol, Add, Mul

    # Prepare some symbols
    a_sym = Symbol('a')
    b_sym = Symbol('b')
    c_sym = Symbol('c')
    d_sym = Symbol('d')

    # === Testing Function‐level associativity ===
    print("=== Testing Function‐level associativity ===")
    Foo = build_operator_class('Foo', ['associative'], arity=2)

    # Left‐nested vs right‐nested
    expr_left  = Foo(Foo(a_sym, b_sym), c_sym)
    expr_right = Foo(a_sym, Foo(b_sym, c_sym))

    print(f" Before grouping:  Foo(Foo(a,b), c) = {expr_left}")
    print(f" Re‐associated:     Foo(a, Foo(b,c)) = {expr_right}")
    assert expr_left == expr_right, "Function‐level associativity failed (semantic)."

    # AST shape
    left_part, right_part = expr_right.args
    assert left_part == a_sym
    assert right_part.func.__name__ == "Foo" and right_part.args == (b_sym, c_sym)
    print("Function‐level associative mixin test passed.\n")

    # Deep nesting test
    expr_deep = Foo(Foo(Foo(a_sym, b_sym), c_sym), d_sym)
    print(f" Deep nested before assoc: Foo(Foo(Foo(a,b),c), d) = {expr_deep}")
    # Should fully right‐associate to Foo(a, Foo(b, Foo(c,d)))
    expected_deep = Foo(a_sym, Foo(b_sym, Foo(c_sym, d_sym)))
    assert expr_deep == expected_deep, "Deep nesting associativity failed."
    print("Deep nesting associative test passed.\n")

    # Negative: operator without mixin should not re‐associate
    print("=== Negative test: no-associative mixin ===")
    Bar = build_operator_class('Bar', [], arity=2)
    expr_bar = Bar(Bar(a_sym, b_sym), c_sym)
    print(f" Bar(Bar(a,b), c) remains left‐nested: args = {expr_bar.args}")
    assert isinstance(expr_bar.args[0], Bar) and expr_bar.args[1] == c_sym, \
        "Non-associative operator should not re-associate."
    print("Negative function‐level associativity test passed.\n")

    # === Testing Symbol‐level associativity for addition ===
    print("=== Testing Symbol‐level associativity for addition ===")
    X = build_symbol('x', ['associative_add'])
    Y = build_symbol('y', ['associative_add'])
    Z = build_symbol('z', ['associative_add'])

    sum_left  = Add(Add(X, Y), Z)
    sum_right = Add(X, Add(Y, Z))
    assert sum_left == sum_right, "Symbol addition should be equal under associativity."
    assert sum_left.args == sum_right.args == (X, Y, Z)
    print("Symbol‐level associative_add test passed.\n")

    # Negative: default Symbol without mixin still flattens by Sympy but carries no key
    print("=== Negative test: addition without mixin key ===")
    x0, y0, z0 = Symbol('x0'), Symbol('y0'), Symbol('z0')
    sum0 = Add(Add(x0, y0), z0)
    print(f" Add(Add(x0,y0),z0) = {sum0}, property_keys on Sum head = {getattr(sum0.func, 'property_keys', None)}")
    assert getattr(sum0.func, 'property_keys', None) is None, \
        "Default symbols should not have 'associative_add' key."
    print("Negative symbol‐level associative_add test passed.\n")

    # === Testing Symbol‐level associativity for multiplication ===
    print("=== Testing Symbol‐level associativity for multiplication ===")
    U = build_symbol('u', ['associative_mul'])
    V = build_symbol('v', ['associative_mul'])
    W = build_symbol('w', ['associative_mul'])

    prod_left  = Mul(Mul(U, V), W)
    prod_right = Mul(U, Mul(V, W))
    assert prod_left == prod_right, "Symbol multiplication should be equal under associativity."
    assert prod_left.args == prod_right.args == (U, V, W)
    print("Symbol‐level associative_mul test passed.\n")

    # Negative: default Symbol without mixin key
    print("=== Negative test: multiplication without mixin key ===")
    u0, v0, w0 = Symbol('u0'), Symbol('v0'), Symbol('w0')
    prod0 = Mul(Mul(u0, v0), w0)
    print(f" Mul(Mul(u0,v0),w0) = {prod0}, property_keys on Prod head = {getattr(prod0.func, 'property_keys', None)}")
    assert getattr(prod0.func, 'property_keys', None) is None, \
        "Default symbols should not have 'associative_mul' key."
    print("Negative symbol‐level associative_mul test passed.\n")

    print("All AssociativeMixin tests (positive and negative) passed.")