# File: symantex/registry.py

from typing import Callable, Dict, List, Tuple, Type
from symantex.mixins.base import PropertyMixin

# Each PatchSpec now includes:
#   (SympyClass, method_name, hook_name, head_extractor, arg_extractor)
PatchSpec = Tuple[Type, str, str, Callable, Callable]


class PropertyRegistry:
    """
    Singleton registry mapping property keys to:
      (description, mixin_class, [patch_specs], original_method)

    - _registry[key]          = (description, mixin_class)
    - _patch_registry[key]    = list of PatchSpec
    - _original_methods[key]  = original, unpatched SympyClass.method_name
    """
    _instance = None

    _registry: Dict[str, Tuple[str, Type]]
    _patch_registry: Dict[str, List[PatchSpec]]
    _original_methods: Dict[str, Callable]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PropertyRegistry, cls).__new__(cls)
            cls._instance._registry = {}
            cls._instance._patch_registry = {}
            cls._instance._original_methods = {}
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
        self._registry[key] = (description, mixin_class)
        self._patch_registry[key] = []
        # Initially, no original method is stored. It will be set in register_patch.

    def register_patch(
        self,
        key: str,
        sympy_class: Type,
        method_name: str,
        hook_name: str,
        head_extractor: Callable,
        arg_extractor: Callable
    ) -> None:
        """
        Associate a monkey-patch spec with an existing property key.

        patch_spec = (
            SympyClass,
            method_to_override,
            hook_method_on_mixin,
            head_extractor,
            arg_extractor
        )

        When this is called, we also capture SympyClass.method_name and store
        it as the "original" unpatched method for later retrieval.
        """
        if key not in self._registry:
            raise KeyError(f"Cannot register patch for unknown property key '{key}'.")

        # Capture the original method if not already done
        if key not in self._original_methods:
            orig = getattr(sympy_class, method_name)
            self._original_methods[key] = orig

        # Append the patch spec
        self._patch_registry[key].append(
            (sympy_class, method_name, hook_name, head_extractor, arg_extractor)
        )

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

    def get_original_method(self, key: str) -> Callable:
        """
        Return the original (unpatched) Sympy method for this property key.
        E.g. for "pull_limit" it returns the real Limit.doit, even after patching.
        Raises if no original was captured or key is unknown.
        """
        try:
            return self._original_methods[key]
        except KeyError:
            raise KeyError(f"No original method stored for property key '{key}'.")

    def all_registered_properties(self) -> Dict[str, str]:
        """Return a dict mapping property_key -> description."""
        return {key: desc for key, (desc, _) in self._registry.items()}

    def all_patch_specs(self) -> List[Tuple[str, Type, str, str, Callable, Callable]]:
        """
        Return a flat list of all registered patch specs in the form:
          (property_key, SympyClass, method_name, hook_name, head_extractor, arg_extractor)
        """
        specs: List[Tuple[str, Type, str, str, Callable, Callable]] = []
        for key, patch_list in self._patch_registry.items():
            for (SymClass, mname, hook, head_ex, arg_ex) in patch_list:
                specs.append((key, SymClass, mname, hook, head_ex, arg_ex))
        return specs


# Module‐level registry instance
_registry = PropertyRegistry()


def register_property(key: str, description: str) -> Callable:
    """
    Decorator to register a mixin class under a given property key.
    Usage:
        @register_property("pull_limit", "description…")
        class PullsLimitMixin(PropertyMixin):
            …
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
    head_extractor: Callable,
    arg_extractor: Callable
) -> None:
    """
    Convenience function to register a patch spec for an existing property key.

    Example:
      register_patch(
          "pull_limit",
          sympy.series.limits.Limit,
          "doit",
          "_eval_limit",
          lambda self: self.args[0],                # head = inner function
          lambda self: (self.args[1],                # var
                        self.args[2],                # point
                        self.args[3])                # direction
      )
    """
    _registry.register_patch(key, sympy_class, method_name, hook_name, head_extractor, arg_extractor)


def get_mixin_for_key(key: str) -> Type:
    return _registry.get_mixin_for_key(key)


def get_original_method(key: str) -> Callable:
    return _registry.get_original_method(key)


def all_registered_properties() -> Dict[str, str]:
    return _registry.all_registered_properties()


def all_patch_specs() -> List[Tuple[str, Type, str, str, Callable, Callable]]:
    return _registry.all_patch_specs()


# ────────────────────────────────────────────────────────────────────────────────
# Self‐test block for registry
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sympy
    from symantex.mixins.base import PropertyMixin

    # Dummy mixin classes
    class DummyMixinA(PropertyMixin):
        pass

    class DummyMixinB(PropertyMixin):
        pass

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
        register_patch(
            "unknown_key",
            sympy.Add,
            "doit",
            "_eval_add_stub",
            lambda self: None,
            lambda self: ()
        )
    except KeyError as e:
        print(f"Correctly caught attempt to patch unknown key: {e}")

    # 3) Register a patch spec for "test_a"
    try:
        register_patch(
            "test_a",
            sympy.Add,
            "__new__",
            "_eval_add_stub",
            lambda self: None,
            lambda self: ()
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

    # 5) Access the original method for "test_a"
    try:
        orig = get_original_method("test_a")
        print(f"Original method for test_a: {orig}")
    except KeyError as e:
        print(f"No original for test_a yet: {e}")

    # 6) Using decorator to register another property
    @register_property("test_c", "Test property C")
    class DummyMixinC(PropertyMixin):
        pass

    print(f"Using decorator, registered test_c: {get_mixin_for_key('test_c').__name__}")
    print(f"All registered properties after decorator: {all_registered_properties()}")

    # 7) test_c should have no patches or originals yet
    try:
        orig_c = get_original_method("test_c")
        print(f"Original method for test_c: {orig_c}")
    except KeyError as e:
        print(f"No original for test_c (as expected): {e}")
