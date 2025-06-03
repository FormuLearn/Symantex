"""
Base definitions and helpers for all mixin classes.
"""

from sympy import default_sort_key, Basic

class PropertyMixin:
    """
    Marker base class for property mixins.
    All mixin classes should inherit from this.

    Provides common utility methods that mixins can leverage.
    """
    def get_property_keys(self):
        """Return the list of property keys attached to this instance, if any."""
        return getattr(self, '_property_keys', [])

    @staticmethod
    def sort_args(args):
        """Return a tuple of args sorted in Sympy's canonical order."""
        # Use Sympy's default_sort_key to sort
        return tuple(sorted(args, key=default_sort_key))

    @classmethod
    def wrap(cls, expr):
        """Utility to re-wrap a Sympy expression in this class's constructor if needed."""
        # Only attempt to wrap Sympy expressions
        if not isinstance(expr, Basic):
            return expr
        try:
            return cls(expr)
        except Exception:
            return expr

# Additional shared utility functions or abstract bases can be added here in the future.


if __name__ == "__main__":
    # Basic tests for PropertyMixin utilities
    from sympy import symbols
    # Test get_property_keys
    class TestMixin(PropertyMixin):
        pass

    # Create a dummy instance and manually set _property_keys
    inst = TestMixin()
    inst._property_keys = ['a', 'b']
    print(f"get_property_keys: {inst.get_property_keys()}")  # Expect ['a', 'b']

    # Test sort_args: use unsorted symbols
    x, y, z = symbols('z y x')
    unsorted = (z, x, y)
    sorted_args = PropertyMixin.sort_args(unsorted)
    print(f"sort_args: {sorted_args}")  # Expect (x, y, z)

    # Test wrap: wrapping a sympy expression
    class WrapMixin(PropertyMixin, type(symbols('u'))):
        def __new__(cls, expr):
            # For testing, simply return the expression multiplied by 2
            from sympy import Mul
            return Mul(expr, 2)

    expr = symbols('u')
    wrapped = WrapMixin.wrap(expr)
    print(f"wrap: {wrapped}")  # Expect 2*u
    # If wrap should not apply to non-Sympy objects
    non_expr = 123
    wrapped_non = WrapMixin.wrap(non_expr)
    print(f"wrap non-expression: {wrapped_non}")  # Expect 123
