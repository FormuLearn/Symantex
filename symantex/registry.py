from typing import Callable, Dict, Tuple, Type
from symantex.mixins.base import PropertyMixin


class PropertyRegistry:
    """
    Singleton registry mapping property keys to (description, mixin_class).
    """
    _instance = None
    _registry: Dict[str, Tuple[str, Type]]  # declare at class level

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PropertyRegistry, cls).__new__(cls)
            cls._instance._registry = {}
        return cls._instance

    def register(self, key: str, description: str, mixin_class: Type) -> None:
        if not issubclass(mixin_class, PropertyMixin):
            raise TypeError(f"Mixin class '{mixin_class.__name__}' must inherit from PropertyMixin.")
        if key in self._registry:
            raise KeyError(f"Property key '{key}' is already registered.")
        self._registry[key] = (description, mixin_class)

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


def get_mixin_for_key(key: str) -> Type:
    return _registry.get_mixin_for_key(key)


def all_registered_properties() -> Dict[str, str]:
    return _registry.all_registered_properties()


if __name__ == "__main__":
    # Simple tests to verify the registry functionality
    from symantex.mixins.base import PropertyMixin

    class DummyMixinA(PropertyMixin):
        pass

    class DummyMixinB(PropertyMixin):
        pass

    class NotAMixin:
        pass

    reg = PropertyRegistry()
    try:
        reg.register("test_a", "Test property A", DummyMixinA)
        print("Registered test_a successfully.")
    except Exception as e:
        print(f"Failed to register test_a: {e}")

    # Attempt to register a class not inheriting PropertyMixin
    try:
        reg.register("test_x", "Invalid mixin class", NotAMixin)
    except TypeError as e:
        print(f"Correctly caught non-PropertyMixin registration: {e}")

    # Attempt duplicate registration to trigger KeyError
    try:
        reg.register("test_a", "Duplicate Test property A", DummyMixinB)
    except KeyError as e:
        print(f"Duplicate registration correctly raised KeyError: {e}")

    # Retrieve mixin and description
    mixin = reg.get_mixin_for_key("test_a")
    desc = reg.get_description_for_key("test_a")
    print(f"Retrieved mixin for test_a: {mixin.__name__}, description: {desc}")

    # List all registered properties
    all_props = reg.all_registered_properties()
    print(f"All registered properties: {all_props}")

    # Using decorator to register
    @register_property("test_b", "Test property B")
    class DummyMixinC(PropertyMixin):
        pass

    print(f"Using decorator, registered test_b: {get_mixin_for_key('test_b').__name__}")
    print(f"All registered properties after decorator: {all_registered_properties()}")
