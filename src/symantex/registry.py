# File: symantex/registry.py

import inspect
from typing import Callable, Dict, List, Optional, Tuple, Type, Union
from symantex.mixins.base import PropertyMixin

# A PatchSpec is now a five‐tuple
PatchSpec = Tuple[
    Type,                            # The Sympy class being patched
    str,                             # method name to override
    str,                             # hook name on the mixin
    Union[str, Callable],            # head_attr (string or callable)
    Optional[Callable]               # arg_extractor (callable or None)
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
    _originals: Dict[str, Callable]
    _categories: Dict[str, str]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PropertyRegistry, cls).__new__(cls)
            cls._instance._registry = {}
            cls._instance._patch_registry = {}
            cls._instance._originals = {}
            cls._instance._categories = {}
        return cls._instance

    def register(self, key: str, description: str, mixin_class: Type) -> None:
        """
        Register a mixin class under `key`, and wrap its __new__ so that
        every new instance (including subclasses) gets `key` in _property_keys.
        """
        if not issubclass(mixin_class, PropertyMixin):
            raise TypeError(f"Mixin class '{mixin_class.__name__}' must inherit from PropertyMixin.")
        if key in self._registry:
            raise KeyError(f"Property key '{key}' is already registered.")

        # store
        self._registry[key] = (description, mixin_class)
        self._patch_registry[key] = []

        orig_new = mixin_class.__new__
        sig = inspect.signature(orig_new)

        def wrapped_new(cls_, *args, **kwargs):
            # 1) If we're constructing *exactly* the mixin itself,
            #    bind to its original __new__ signature.
            if cls_ is mixin_class:
                try:
                    bound = sig.bind_partial(cls_, *args, **kwargs)
                    call_args = list(bound.arguments.values())
                    obj = orig_new(*call_args)
                except Exception:
                    # fallback to simplest
                    try:
                        obj = orig_new(cls_)
                    except Exception:
                        obj = object.__new__(cls_)
            else:
                # 2) cls_ is some subclass (e.g. your generated Symbol/Function).  Find
                #    where mixin_class sits in *that* MRO, and delegate to the very
                #    next __new__ after it (so that Symbol.__new__ or Function.__new__
                #    actually runs and sets up _args/_nargs correctly).
                mro = cls_.__mro__
                idx = mro.index(mixin_class)

                for base in mro[idx+1:]:
                    # ← skip *any* mixin‐only classes so we get to Function.__new__
                    if issubclass(base, PropertyMixin):
                        continue

                    base_new = getattr(base, "__new__", None)
                    # ← object.__new__ is not what we want here
                    if base_new is None or base_new is object.__new__:
                        continue

                    try:
                        obj = base_new(cls_, *args, **kwargs)
                        break
                    except TypeError:
                        continue
                else:
                    obj = object.__new__(cls_)


            # 3) Finally, attach or extend the _property_keys list
            existing = getattr(obj, "_property_keys", [])
            obj._property_keys = existing + [key]
            return obj

        # install
        mixin_class.__new__ = staticmethod(wrapped_new)

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
        Associate a monkey‐patch spec with an existing property key.
        """
        if key not in self._registry:
            raise KeyError(f"Cannot register patch for unknown property key '{key}'.")
        self._patch_registry[key].append(
            (sympy_class, method_name, hook_name, head_attr, arg_extractor)
        )

    def store_original_method(self, key: str, method: Callable) -> None:
        """Save the original (unpatched) method under this property key."""
        self._originals[key] = method

    def get_original_method(self, key: str) -> Callable:
        """Return the original method that was patched for this key."""
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
        
    def assign_category(self, key: str, category: str) -> None:
        """Tag a registered property with a category (e.g. 'default', 'advanced')."""
        if key not in self._registry:
            raise KeyError(f"Property key '{key}' is not registered.")
        self._categories[key] = category

    def properties_in_category(self, category: str) -> list[str]:
        """Return all property-keys tagged with `category`."""
        return [k for k, cat in self._categories.items() if cat == category]


    def all_registered_properties(self) -> Dict[str, str]:
        """Return a dict mapping property_key → description."""
        return {k: desc for k, (desc, _) in self._registry.items()}

    def all_patch_specs(self) -> List[Tuple[str, Type, str, str, Union[str, Callable], Optional[Callable]]]:
        """Return all registered patch specs as a flat list."""
        specs = []
        for key, patches in self._patch_registry.items():
            for spec in patches:
                specs.append((key, *spec))
        return specs


# Module‐level convenience functions and registry instance

_registry = PropertyRegistry()

def register_property(
    key: str,
    description: str,
    *,
    category: str = "default"
) -> Callable:
    """
    Register a mixin under `key`, with a human description *and* a category tag.
    """
    def decorator(cls):
        _registry.register(key, description, cls)
        _registry.assign_category(key, category)
        return cls
    return decorator


def register_patch(
    key: str,
    sympy_class: Type,
    method_name: str,
    hook_name: str,
    head_attr: Union[str, Callable],
    arg_extractor: Optional[Callable] = None
) -> None:
    _registry.register_patch(key, sympy_class, method_name, hook_name, head_attr, arg_extractor)

def store_original_method(key: str, method: Callable) -> None:
    _registry.store_original_method(key, method)

def get_original_method(key: str) -> Callable:
    return _registry.get_original_method(key)

def get_mixin_for_key(key: str) -> Type:
    return _registry.get_mixin_for_key(key)

def all_registered_properties() -> Dict[str, str]:
    return _registry.all_registered_properties()

def all_patch_specs():
    return _registry.all_patch_specs()


if __name__ == "__main__":
    import sympy
    from sympy import Add
    from symantex.mixins.base import PropertyMixin


    # ———————————————————————————————————————————————————————————————
    # Dummy mixins registered via decorator (with explicit categories)
    # ———————————————————————————————————————————————————————————————
    @register_property("test_a", "A desc", category="unit")
    class DummyMixinA(PropertyMixin):
        def __new__(cls, x):
            inst = super().__new__(cls)
            return inst

    @register_property("test_b", "B desc", category="unit")
    class DummyMixinB(PropertyMixin):
        pass

    print("All keys:", list(all_registered_properties().keys()))
    # Expect to see 'test_a' and 'test_b' in the full registry
    assert "test_a" in all_registered_properties()
    assert "test_b" in all_registered_properties()

    print("Unit-category keys:", _registry.properties_in_category("unit"))
    # Both dummy tests should live in the 'unit' category
    assert set(_registry.properties_in_category("unit")) == {"test_a", "test_b"}

    # ———————————————————————————————————————————————————————————————
    # 2) Patch‐unknown still raises KeyError
    # ———————————————————————————————————————————————————————————————
    try:
        register_patch("nope", sympy.Add, "doit", "_eval", "args")
    except KeyError as e:
        print("Caught expected KeyError for unknown patch:", e)
    else:
        raise RuntimeError("register_patch('nope',…) should have raised KeyError")

    # ———————————————————————————————————————————————————————————————
    # 3) __new__ wrapping: instances get their key in _property_keys
    # ———————————————————————————————————————————————————————————————
    a = DummyMixinA(42)
    b = DummyMixinB()
    print("A._property_keys:", a._property_keys)
    print("B._property_keys:", b._property_keys)
    assert a._property_keys == ["test_a"]
    assert b._property_keys == ["test_b"]

    print("Self‐test passed.")
