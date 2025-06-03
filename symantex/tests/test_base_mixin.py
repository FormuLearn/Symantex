if __name__ == "__main__":
    # Basic tests for get_property_keys, has_property, sort_args, wrap
    from sympy import symbols, Limit, Derivative
    from symantex.registry import register_property, register_patch
    from symantex.factory import build_operator_class
    from symantex.mixins.base import PropertyMixin

    x, y, z = symbols("x y z")

    # 1) Test get_property_keys & has_property
    class Dummy(PropertyMixin):
        pass

    inst = Dummy()
    inst._property_keys = ["foo", "bar"]
    print("get_property_keys:", inst.get_property_keys())       # → ['foo','bar']
    print("has_property('foo'):", inst.has_property("foo"))     # → True
    print("has_property('baz'):", inst.has_property("baz"))     # → False

    # 2) Test sort_args
    unsorted = (z, x, y)
    print("sort_args:", PropertyMixin.sort_args(unsorted))      # → (x, y, z)

    # 3) Test wrap
    class WrapMul(PropertyMixin, type(x)):
        def __new__(cls, expr):
            from sympy import Mul
            return Mul(expr, 2)

    expr = symbols("u")
    print("wrap:", WrapMul.wrap(expr))         # → 2*u
    print("wrap vs non-expr:", WrapMul.wrap(123))  # → 123

     # 4) “DemoLimit” as a proper decorator:
    @register_property("demo_limit", "demo")
    class DemoLimit(PropertyMixin):
        def _eval_limit(self, var, point, direction):
            inner_node = Limit(self.args[0], var, point, direction)
            return self.call_original("demo_limit", inner_node)

    # Now we can register the patch spec, because "demo_limit" is already known:
    register_patch(
        "demo_limit",
        Limit,
        "doit",
        "_eval_limit",
        lambda self: self.args[0],                  # head 
        lambda self: (self.args[1], self.args[2], self.args[3])  # (var,point,direction)
    )

    from symantex._patches import apply_all_patches
    apply_all_patches()

    F = build_operator_class("F", ["demo_limit"], arity=1)
    expr = Limit(F(x**2), x, 0, "+")
    print("call_original demo limit:", expr.doit())  # → F(0)

    # ────────────────────────────────────────────────
    # 5) Test “original call” for a derivative mixin
    # ────────────────────────────────────────────────
    @register_property("demo_deriv", "demo")
    class DemoDeriv(PropertyMixin):
        def _eval_derivative(self, var):
            inner_node = Derivative(self.args[0], var)
            return self.call_original("demo_deriv", inner_node)

    register_patch(
        "demo_deriv",
        Derivative,
        "doit",
        "_eval_derivative",
        lambda self: self.args[0],
        lambda self: (self.args[1],)
    )

    apply_all_patches()

    H = build_operator_class("H", ["demo_deriv"], arity=1)
    expr2 = Derivative(H(x**3), x)
    print("call_original demo deriv:", expr2.doit())  # → H(3*x**2)
