# File: symantex/mixins/base.py

from sympy import default_sort_key, Basic
from typing import Any, Tuple


class PropertyMixin:
    """
    Marker base class for property mixins.
    """

    def get_property_keys(self) -> list[str]:
        return getattr(self, "_property_keys", [])

    def has_property(self, key: str) -> bool:
        inst_keys = getattr(self, "_property_keys", None)
        if inst_keys is not None and key in inst_keys:
            return True

        cls_keys = getattr(getattr(self, "func", None), "property_keys", None)
        if cls_keys is not None and key in cls_keys:
            return True

        return False

    def call_original(self, key: str, node: Any, *args, **kwargs) -> Any:
        from symantex.registry import get_original_method

        # First check for head.func.__orig_<method>
        orig_attr = getattr(getattr(node, "func", None), f"__orig_{key}", None)
        if orig_attr is not None:
            return orig_attr(node, *args, **kwargs)

        # Otherwise fetch from registry
        try:
            orig_method = get_original_method(key)
        except KeyError:
            raise RuntimeError(f"No original method stored for property '{key}'")
        return orig_method(node, *args, **kwargs)

    @staticmethod
    def sort_args(args: Tuple) -> Tuple:
        return tuple(sorted(args, key=default_sort_key))

    @classmethod
    def wrap(cls, expr: Any) -> Any:
        if not isinstance(expr, Basic):
            return expr
        try:
            return cls(expr)
        except Exception:
            return expr

