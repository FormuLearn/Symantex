# symantex/factory.py

from typing import List, Optional, Tuple, Type, Dict
import sympy as sp
from sympy import Symbol, MatrixSymbol, Function
from symantex.registry import get_mixin_for_key

# === DO NOT REMOVE IMPORT === #
import symantex._patches # To incorporate monkeypatches to make limits work with _eval_limit


def _dedupe_classes(classes: List[Type]) -> List[Type]:
    """Return a list of unique classes preserving original order."""
    seen = set()
    unique = []
    for cls in classes:
        if cls not in seen:
            unique.append(cls)
            seen.add(cls)
    return unique


def build_symbol(name: str, property_keys: List[str], shape: Optional[Tuple[int, int]] = None) -> sp.Expr:
    """
    Build a Sympy Symbol or MatrixSymbol subclassed with mixins based on property_keys.

    - If shape is provided as (n, m), dynamically creates a subclass of MatrixSymbol with mixins and returns an instance.
    - Otherwise, dynamically creates a subclass of Symbol with mixins. Commutativity should be implemented via a dedicated mixin (e.g., NonCommutativeMixin).

    The returned symbol instance has a '_property_keys' attribute listing all assigned properties.
    """
    # Collect mixin classes
    mixin_classes: List[Type] = []
    for key in property_keys:
        mixin = get_mixin_for_key(key)
        mixin_classes.append(mixin)
    # Remove duplicate mixins
    mixin_classes = _dedupe_classes(mixin_classes)

    if shape is not None:
        if not (isinstance(shape, tuple) and len(shape) == 2 and all(isinstance(x, int) for x in shape)):
            raise ValueError("Shape must be a tuple of two integers.")
        # Validate mixins are compatible with MatrixSymbol
        for mixin in mixin_classes:
            if not issubclass(mixin, MatrixSymbol):
                raise TypeError(f"Mixin class '{mixin.__name__}' is not compatible with MatrixSymbol.")
        # Create dynamic subclass of MatrixSymbol
        bases = tuple(mixin_classes + [MatrixSymbol])
        class_name = f"Symbol_{name}_Matrix"
        namespace: Dict[str, object] = {}
        new_class = type(class_name, bases, namespace)
        # Instantiate: MatrixSymbol requires (name, rows, cols)
        instance = new_class(name, shape[0], shape[1])
        instance._property_keys = property_keys[:]  # attach for future introspection
        return instance

    # Create dynamic subclass of Symbol
    bases = tuple(mixin_classes + [Symbol])
    class_name = f"Symbol_{name}"  # unique class name
    namespace: Dict[str, object] = {}
    new_class = type(class_name, bases, namespace)
    # Instantiate: Symbol takes (name)
    instance = new_class(name)
    instance._property_keys = property_keys[:]  # attach for future introspection
    return instance


def build_operator_class(operator_name: str,
                         property_keys: List[str],
                         arity: int,
                         pretty_str: Optional[str] = None) -> Type[Function]:
    """
    Dynamically construct a Sympy Function subclass with mixins based on property_keys.

    - operator_name: name of the new operator class.
    - property_keys: list of registered property keys; mixin classes are looked up in the registry.
    - arity: number of arguments the function takes.
    - pretty_str: optional string to use when printing; defaults to operator_name.

    The returned class has a class attribute 'property_keys' and nargs set to enforce arity.
    Additional algebraic properties (associative, distributive, identity) can be implemented via mixins.
    """
    # Collect mixin classes
    mixin_classes: List[Type] = []
    for key in property_keys:
        mixin = get_mixin_for_key(key)
        mixin_classes.append(mixin)
    # Remove duplicate mixins
    mixin_classes = _dedupe_classes(mixin_classes)
    # Always include Sympy Function
    bases = tuple(mixin_classes + [Function])
    # Prepare namespace dict
    namespace: Dict[str, object] = {'property_keys': property_keys[:]}
    if pretty_str:
        def __repr__(self):
            return f"{pretty_str}{tuple(self.args)}"
        namespace['__repr__'] = __repr__
    # Set nargs (arity) in namespace so sympy picks it up
    namespace['nargs'] = arity
    # Create the new class
    new_class = type(operator_name, bases, namespace)
    return new_class


if __name__ == "__main__":
    # Basic tests for factory functions
    from symantex.mixins.base import PropertyMixin
    from symantex.registry import PropertyRegistry

    reg = PropertyRegistry()

    # Define symbol mixins inheriting from Symbol
    class DummySymMixin(PropertyMixin, Symbol):
        """Example mixin that could override Symbol behavior."""
        pass

    class DummySymMixinNC(PropertyMixin, Symbol):
        """Example mixin for non-commutative symbol."""
        def __new__(cls, name, **kwargs):
            return super().__new__(cls, name, commutative=False)

    class DummyMatrixMixin(PropertyMixin, MatrixSymbol):
        """Example mixin for MatrixSymbol compatibility."""
        pass

    # Register mixins
    reg.register("identity", "Symbol acts as identity under addition", DummySymMixin)
    reg.register("non_commutative", "Symbol is non-commutative", DummySymMixinNC)
    reg.register("matrix_identity", "MatrixSymbol identity property", DummyMatrixMixin)

    # Create a Symbol with a mixin
    sym = build_symbol("x", ["identity"])
    print(f"Symbol x: {sym}, properties: {sym._property_keys}")

    # Create a Symbol with multiple mixins (non-commutative then identity)
    sym_nc = build_symbol("y", ["non_commutative", "identity"] )
    print(f"Symbol y: {sym_nc}, is_commutative: {sym_nc.is_commutative}, properties: {sym_nc._property_keys}")

    # Create a MatrixSymbol with a compatible mixin
    mat = build_symbol("M", ["matrix_identity"], (2, 2))
    print(f"MatrixSymbol M: {mat}, shape: ({mat.shape[0]}, {mat.shape[1]}), properties: {mat._property_keys}")

    # Operator mixin tests
    class DummyOpMixin(PropertyMixin, Function):
        """Example operator mixin."""
        pass

    reg.register("dummy_op", "Dummy operator mixin", DummyOpMixin)
    reg.register("associative", "Associative operator", DummyOpMixin)

    OpClass = build_operator_class("MyOp", ["dummy_op", "associative"], 2, pretty_str="MyOpPretty")
    print(f"Created operator class: {OpClass.__name__}, bases: {OpClass.__mro__}, property_keys: {OpClass.property_keys}")

    a, b = Symbol('a'), Symbol('b')
    expr = OpClass(a, b)
    print(f"Operator expression repr: {repr(expr)}")
