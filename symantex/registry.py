# File: symantex/registry.py

from typing import Callable, Dict, List, Tuple, Type, Union, Optional
from symantex.mixins.base import PropertyMixin

# A PatchSpec is a five‐tuple:
#   (SympyClass, method_to_override, hook_method_on_mixin, head_attr)
PatchSpec = Tuple[
                Type, # The sympy class being patched
                str, # method being overridden
                str, # hook name on the mixin
                Union[str, Callable], # head_attr (either attribute‐name or callable(self)->Expression)
                Union[str, Callable], # arg_extractor (callable(self)->tuple of hook arguments, or None)
            ]


class PropertyRegistry:
    """
    Singleton registry mapping property keys to:
      (description, mixin_class)
    and storing patch specs separately.
    Also stores original methods for each property key so mixins can call them.
    """
    _instance = None

    _registry: Dict[str, Tuple[str, Type]]
    _patch_registry: Dict[str, List[PatchSpec]]
    _originals: Dict[str, Callable]  # map property_key -> original method

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PropertyRegistry, cls).__new__(cls)
            cls._instance._registry = {}
            cls._instance._patch_registry = {}
            cls._instance._originals = {}
        return cls._instance

    def register(self, key: str, description: str, mixin_class: Type) -> None:
        """
        Register a mixin class under a given property key.
        Raises if mixin_class is not a subclass of PropertyMixin, or if key already exists.
        """
        if not issubclass(mixin_class, PropertyMixin):
            raise TypeError(f"Mixin class '{mixin_class.__name__}' must inherit from PropertyMixin.")
        if key in self._registry:
            raise KeyError(f"Property key '{key}' is already registered.")

        # Store description and mixin_class
        self._registry[key] = (description, mixin_class)
        # Initialize an empty list of patch specs
        self._patch_registry[key] = []

    def register_patch(
        self,
        key: str,
        sympy_class: Type,
        method_name: str,
        hook_name: str,
        head_attr: Union[str, Callable],
        arg_extractor: Optional[Callable] = None
    ) -> None:
        """
        Associate a monkey-patch spec with an existing property key.

        patch_spec = (SympyClass, method_name, hook_name, head_attr, arg_extractor)

        - `sympy_class`: the Sympy class whose method is being overridden
          (e.g. sympy.Derivative, sympy.Limit, sympy.Integral, etc.)

        - `method_name`: the name of the method we are wrapping (e.g. "doit")

        - `hook_name`: the name of the mixin method on the operator that should be called
                       (e.g. "_eval_limit", "_eval_derivative", "_eval_Integral")

        - `head_attr`: either
            * a `str` naming an attribute on `self` (e.g. "expr" or "function"),
            * or a callable `f(self)->Expression` that extracts the “head” from `self`.

        - `arg_extractor`: a callable `f(self)->tuple` that returns exactly the
            positional arguments that the mixin’s hook expects.
            If `None`, the mixin will be called with no extra arguments: i.e. `hook(head)`.

        Raises KeyError if `key` has not been registered yet.
        """
        if key not in self._registry:
            raise KeyError(f"Cannot register patch for unknown property key '{key}'.")
        # Append the 5‐tuple to the patch‐registry
        self._patch_registry[key].append((sympy_class, method_name, hook_name, head_attr, arg_extractor))

    def store_original_method(self, key: str, method: Callable) -> None:
        """
        Save the original (unpatched) method under this property key.
        Mixins can retrieve it via get_original_method(key).
        """
        self._originals[key] = method

    def get_original_method(self, key: str) -> Callable:
        """
        Return the original method that was patched for this key.
        Raises if no original was stored.
        """
        try:
            return self._originals[key]
        except KeyError:
            raise KeyError(f"No original method stored for property key '{key}'.")

    def get_mixin_for_key(self, key: str) -> Type:
        """Return the mixin class for a given property key."""
        try:
            return self._registry[key][1]
        except KeyError:
            raise KeyError(f"Property key '{key}' is not registered.")

    def get_description_for_key(self, key: str) -> str:
        """Return the description for a given property key."""
        try:
            return self._registry[key][0]
        except KeyError:
            raise KeyError(f"Property key '{key}' is not registered.")

    def all_registered_properties(self) -> Dict[str, str]:
        """Return a dict mapping property_key -> description."""
        return {key: desc for key, (desc, _) in self._registry.items()}

    def all_patch_specs(self) -> List[Tuple[str, Type, str, str, str, Callable]]:
        """
        Return a flat list of all registered patch specs in the form:
          (property_key, SymClass, method_name, hook_name, head_attr)
        """
        specs: List[Tuple[str, Type, str, str, str, Callable]] = []
        for key, patch_list in self._patch_registry.items():
            for (SymClass, mname, hook, head_attr, arg_extractor) in patch_list:
                specs.append((key, SymClass, mname, hook, head_attr, arg_extractor))
        return specs


# Module‐level registry instance
_registry = PropertyRegistry()


def register_property(key: str, description: str) -> Callable:
    """
    Decorator to register a mixin class under a given property key.
    """
    def decorator(mixin_class: Type) -> Type:
        _registry.register(key, description, mixin_class)
        return mixin_class
    return decorator


def register_patch(
    key: str,
    sympy_class: Type,
    method_name: str,
    hook_name: str,
    head_attr: Union[str, Callable],
    arg_extractor: Optional[Callable] = None
) -> None:
    """
    Convenience function to register a patch spec for an existing property key.

    Example:

        register_patch(
            "pull_limit",
            sympy.Limit,
            "doit",
            "_eval_limit",
            lambda self: self.args[0],                # head = the inner function
            lambda self: (self.args[1], self.args[2], self.args[3])  # (var, point, direction)
        )
    """
    _registry.register_patch(key, sympy_class, method_name, hook_name, head_attr, arg_extractor)


def store_original_method(key: str, method: Callable) -> None:
    """
    Convenience function to store an original method for a property key.
    """
    _registry.store_original_method(key, method)


def get_original_method(key: str) -> Callable:
    """
    Convenience function to retrieve the original method for a property key.
    """
    return _registry.get_original_method(key)


def get_mixin_for_key(key: str) -> Type:
    return _registry.get_mixin_for_key(key)


def all_registered_properties() -> Dict[str, str]:
    return _registry.all_registered_properties()


def all_patch_specs() -> List[Tuple[str, Type, str, str, str]]:
    return _registry.all_patch_specs()


if __name__ == "__main__":
    import sympy
    from sympy import Add
    from symantex.mixins.base import PropertyMixin

    # Dummy mixin classes for testing
    class DummyMixinA(PropertyMixin):
        def __new__(cls, x):
            return super().__new__(cls, x)

    class DummyMixinB(PropertyMixin):
        pass

    reg = PropertyRegistry()

    # 1) Register two properties
    try:
        reg.register("test_a", "Test property A", DummyMixinA)
        print("Registered test_a successfully.")
    except Exception as e:
        print(f"Failed to register test_a: {e}")

    try:
        reg.register("test_b", "Test property B", DummyMixinB)
        print("Registered test_b successfully.")
    except Exception as e:
        print(f"Failed to register test_b: {e}")

    # 2) Attempt to register a patch for an unknown key
    try:
        register_patch("unknown_key", sympy.Add, "doit", "_eval_add_stub", "args")
    except KeyError as e:
        print(f"Correctly caught attempt to patch unknown key: {e}")

    # 3) Register a patch spec for "test_a"
    try:
        register_patch(
            "test_a",
            sympy.Add,
            "__new__",
            "_eval_add_stub",
            "args",                # head_attr
            lambda self: tuple()   # arg_extractor (just an example)
        )
        print("Registered patch spec for test_a.")
    except Exception as e:
        print(f"Failed to register patch spec for test_a: {e}")

    # 4) Retrieve mixin and patch specs
    mix_a = get_mixin_for_key("test_a")
    print(f"Retrieved mixin for test_a: {mix_a.__name__}")

    all_props = all_registered_properties()
    print(f"All registered properties: {all_props}")

    specs = all_patch_specs()
    print("All patch specs:", specs)

    # 5) Using decorator to register another property
    @register_property("test_c", "Test property C")
    class DummyMixinC(PropertyMixin):
        pass

    print(f"Using decorator, registered test_c: {get_mixin_for_key('test_c').__name__}")
    print(f"All registered properties after decorator: {all_registered_properties()}")

    # 6) Verify that __new__ was wrapped:
    inst_a = DummyMixinA(42)
    print(f"inst_a._property_keys (should contain 'test_a'): {inst_a._property_keys}")

    inst_b = DummyMixinB()
    print(f"inst_b._property_keys (should contain 'test_b'): {inst_b._property_keys}")

    inst_c = DummyMixinC()
    print(f"inst_c._property_keys (should contain 'test_c'): {inst_c._property_keys}")

    print("Self‐test completed.")