# File: symantex/registry.py

from typing import Callable, Dict, List, Tuple, Type
from symantex.mixins.base import PropertyMixin

# A patch specification needs five pieces:
#   1. property_key        (e.g. "pull_limit")
#   2. SympyClass          (e.g. sympy.series.limits.Limit)
#   3. method_name         (e.g. "doit")
#   4. hook_name           (e.g. "_eval_limit" on the mixin)
#   5. head_attr           (how to get the head from 'self', e.g. "function" or "expr")
#
# We'll store patch specs internally as a dict: key -> List[PatchSpec]
PatchSpec = Tuple[Type, str, str, str]  # (SympyClass, method_name, hook_name, head_attr)


class PropertyRegistry:
    """
    Singleton registry mapping property keys to:
      (description, mixin_class, [patch_specs], original_method)

    Where:
      - _registry[key] = (description, mixin_class)
      - _patch_registry[key] = list of PatchSpec tuples
      - _originals[key] = the original un-patched method for that key (Callable)
    """
    _instance = None

    _registry: Dict[str, Tuple[str, Type]]
    _patch_registry: Dict[str, List[PatchSpec]]
    _originals: Dict[str, Callable]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PropertyRegistry, cls).__new__(cls)
            # key -> (description, mixin_class)
            cls._instance._registry = {}
            # key -> List[PatchSpec]
            cls._instance._patch_registry = {}
            # key -> original method (before patching)
            cls._instance._originals = {}
        return cls._instance

    def register(self, key: str, description: str, mixin_class: Type) -> None:
        """
        Register a mixin class under a given property key.
        Raises if mixin_class is not a subclass of PropertyMixin, or if key already exists.

        As part of registration, wrap mixin_class.__new__ so that every new instance
        has this property 'key' appended into its `_property_keys` list.
        """
        if not issubclass(mixin_class, PropertyMixin):
            raise TypeError(f"Mixin class '{mixin_class.__name__}' must inherit from PropertyMixin.")
        if key in self._registry:
            raise KeyError(f"Property key '{key}' is already registered.")

        # 1) Store description and mixin_class
        self._registry[key] = (description, mixin_class)
        # 2) Initialize empty patch list
        self._patch_registry[key] = []
        # 3) Initialize “original” slot to None; it will be set when we actually patch
        self._originals[key] = None

        # 4) Wrap the mixin_class.__new__ so that every instance of mixin_class
        #    automatically has 'key' appended to its `_property_keys` list.
        orig_new = mixin_class.__new__

        def wrapped_new(cls, *args, **kwargs):
            # Call the original __new__ (which may return an instance)
            obj = orig_new(cls, *args, **kwargs)

            # Append `key` to its existing list (if any), or create a new list.
            if hasattr(obj, "_property_keys"):
                existing = getattr(obj, "_property_keys", [])
                obj._property_keys = existing + [key]
            else:
                setattr(obj, "_property_keys", [key])
            return obj

        mixin_class.__new__ = staticmethod(wrapped_new)

    def register_patch(
        self,
        key: str,
        sympy_class: Type,
        method_name: str,
        hook_name: str,
        head_attr: str
    ) -> None:
        """
        Associate a monkey-patch spec with an existing property key.

        patch_spec = (SympyClass, method_to_override, hook_method_on_mixin, head_attr)

        head_attr is a string: the attribute name on 'self' where the head lives.
          - For Limit.doit: head_attr = "function"
          - For Derivative.doit: head_attr = "expr"
          - For Integral.doit: head_attr = "function"
          - For Sum.doit: head_attr = "function"
        """
        if key not in self._registry:
            raise KeyError(f"Cannot register patch for unknown property key '{key}'.")
        self._patch_registry[key].append((sympy_class, method_name, hook_name, head_attr))

    def store_original_method(self, key: str, original: Callable) -> None:
        """
        Save the original (unpatched) method for property 'key'.
        This must be called exactly once, just before we actually overwrite it.
        """
        if key not in self._registry:
            raise KeyError(f"Cannot store original for unknown property key '{key}'.")
        # Only store if not already set
        if self._originals[key] is None:
            self._originals[key] = original

    def get_original_method(self, key: str) -> Callable:
        """
        Retrieve the original un-patched method for property 'key'.
        Raises if no original was stored.
        """
        if key not in self._registry:
            raise KeyError(f"No such property key '{key}'.")
        orig = self._originals[key]
        if orig is None:
            raise KeyError(f"No original method stored for property key '{key}'.")
        return orig

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

    def all_patch_specs(self) -> List[Tuple[str, Type, str, str, str]]:
        """
        Return a flat list of all registered patch specs in the form:
          (property_key, SympyClass, method_name, hook_name, head_attr)
        """
        specs: List[Tuple[str, Type, str, str, str]] = []
        for key, patch_list in self._patch_registry.items():
            for (SymClass, mname, hook, head_attr) in patch_list:
                specs.append((key, SymClass, mname, hook, head_attr))
        return specs


# Module-level registry instance
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
    head_attr: str
) -> None:
    """
    Convenience function to register a patch spec for an existing property key.
    Example:
      register_patch(
          "pull_limit",
          sympy.series.limits.Limit,
          "doit",
          "_eval_limit",
          "function"
      )
    """
    _registry.register_patch(key, sympy_class, method_name, hook_name, head_attr)


def store_original_method(key: str, original: Callable) -> None:
    """
    Convenience wrapper around PropertyRegistry.store_original_method.
    """
    _registry.store_original_method(key, original)


def get_original_method(key: str) -> Callable:
    """
    Convenience wrapper around PropertyRegistry.get_original_method.
    """
    return _registry.get_original_method(key)


def get_mixin_for_key(key: str) -> Type:
    return _registry.get_mixin_for_key(key)


def all_registered_properties() -> Dict[str, str]:
    return _registry.all_registered_properties()


def all_patch_specs() -> List[Tuple[str, Type, str, str, str]]:
    return _registry.all_patch_specs()


# ────────────────────────────────────────────────────────────────────────────────
# Self-test block for registry
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sympy
    from symantex.mixins.base import PropertyMixin

    # Dummy mixin classes
    class DummyMixinA(PropertyMixin):
        # no explicit __new__ override
        pass

    class DummyMixinB(PropertyMixin):
        # explicit __new__ override
        def __new__(cls, x):
            inst = super().__new__(cls, x)
            return inst

    # 1) Register two properties
    reg = PropertyRegistry()
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
        register_patch("test_a", sympy.Add, "__new__", "_eval_add_stub", "args")
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

    # 5) Now store an “original” method for test_a, then retrieve it
    try:
        store_original_method("test_a", sympy.Add.__new__)
        orig = get_original_method("test_a")
        print(f"Original for test_a: {orig}")
    except Exception as e:
        print(f"Error with get_original_method: {e}")

    # 6) Using decorator to register another property
    @register_property("test_c", "Test property C")
    class DummyMixinC(PropertyMixin):
        pass

    print(f"Using decorator, registered test_c: {get_mixin_for_key('test_c').__name__}")
    print(f"All registered properties after decorator: {all_registered_properties()}")

    # 7) Verify that __new__ was wrapped:
    inst_a = DummyMixinA()    # original __new__ returned an object
    print(f"inst_a._property_keys (should contain 'test_a'): {inst_a._property_keys}")

    inst_c = DummyMixinC()    # wrapper __new__ should have appended 'test_c'
    print(f"inst_c._property_keys (should contain 'test_c'): {inst_c._property_keys}")
