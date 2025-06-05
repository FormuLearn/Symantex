# File: symantex/_patches.py

import functools
import sympy
from typing import Dict, List, Tuple, Type, Union, Callable
from symantex.registry import all_patch_specs, store_original_method, get_original_method

# ────────────────────────────────────────────────────────────────────────────────
# We rebuild this mapping on each call to apply_all_patches().
# It maps (SymClass, method_name) → list of (property_key, hook_name, head_attr).
#
# head_attr can now be either:
#   - a string (the attribute name on 'self'), or
#   - a callable f(self) → the “head” expression
# ────────────────────────────────────────────────────────────────────────────────

# (Reconstructed in apply_all_patches)
_METHOD_PATCHES: Dict[
    Tuple[Type, str],
    List[Tuple[str, str, Union[str, Callable]]]
] = {}


def _build_method_patches():
    """
    Reconstruct `_METHOD_PATCHES` from the current `all_patch_specs()`.
    Each entry is (prop_key, SymClass, method_name, hook_name, head_attr).
    """
    global _METHOD_PATCHES
    _METHOD_PATCHES = {}
    for prop_key, SymClass, method_name, hook_name, head_attr in all_patch_specs():
        key = (SymClass, method_name)
        _METHOD_PATCHES.setdefault(key, []).append((prop_key, hook_name, head_attr))


def _make_combined_wrapper(
    SymClass: Type,
    method_name: str,
    specs: List[Tuple[str, str, Union[str, Callable]]]
):
    """
    Create a single wrapper for `SymClass.method_name` that checks
    all registered `(property_key, hook_name, head_attr)` in order.
    """

    original_method = getattr(SymClass, method_name)

    @functools.wraps(original_method)
    def patched(self, *args, **kwargs):
        # 1) Attempt to extract “head” (the inner operator/function) via head_attr.
        head = None
        for _, _, head_attr in specs:
            if isinstance(head_attr, str):
                if hasattr(self, head_attr):
                    head = getattr(self, head_attr)
                    break
            else:
                # assume head_attr is callable(self) -> expression
                try:
                    head = head_attr(self)
                    break
                except Exception:
                    continue

        # 2) If no head was found, just call the original method.
        if head is None:
            return original_method(self, *args, **kwargs)

        # 3) Gather all property‐keys from:
        #    a) instance‐level: head._property_keys
        #    b) mixin on the class: head.func._property_keys
        #    c) operator‐class: head.func.property_keys
        prop_keys: List[str] = []
        if hasattr(head, "_property_keys"):
            prop_keys += getattr(head, "_property_keys", [])
        if hasattr(head, "func") and hasattr(head.func, "_property_keys"):
            prop_keys += getattr(head.func, "_property_keys", [])
        if hasattr(head, "func") and hasattr(head.func, "property_keys"):
            prop_keys += getattr(head.func, "property_keys", [])


        # 4) Iterate through each patch spec in registration order
        for prop_key, hook_name, head_attr in specs:
            if prop_key in prop_keys:
                # We found a matching property-key
                head2 = None
                if isinstance(head_attr, str):
                    head2 = getattr(self, head_attr, None)
                else:
                    head2 = head_attr(self)

                hook = getattr(head2.func, hook_name, None)
                if hook is None:
                    continue  # this mixin has no _eval_* for this SymClass

                # Attach the original unpatched method under "__orig_{method_name}"
                try:
                    orig = get_original_method(prop_key)
                    setattr(head2.func, f"__orig_{method_name}", orig)
                except KeyError:
                    pass

                # Build hook_args depending on the SymClass
                if SymClass is sympy.Derivative:
                    deriv_arg = self.args[1]
                    if isinstance(deriv_arg, tuple):
                        var = deriv_arg[0]
                    else:
                        var = deriv_arg
                    hook_args = (var,)
                elif SymClass is sympy.Limit:
                    _, var, point, direction = self.args
                    hook_args = (var, point, direction)
                elif SymClass is sympy.Integral:
                    ivar = self.args[1]
                    if isinstance(ivar, tuple):
                        var = ivar[0]
                    else:
                        var = ivar
                    hook_args = (var,)
                else:
                    hook_args = ()

                return hook(head2, *hook_args, **kwargs)


        # 5) No patch‐key matched. If `head.func` has ANY attribute "property_keys",
        #    that means it’s a “custom operator,” so return `self` (unevaluated).
        if hasattr(head, "func") and hasattr(head.func, "property_keys"):
            return self

        return original_method(self, *args, **kwargs)

    return patched


def apply_all_patches():
    """
    1) Rebuild the patch‐spec mapping from all_patch_specs()
    2) For each (SymClass, method_name), store the original method under each prop_key
    3) Install a combined wrapper for that SymClass.method_name
    """
    _build_method_patches()

    for (SymClass, method_name), specs in _METHOD_PATCHES.items():
        original = getattr(SymClass, method_name)
        from symantex.registry import store_original_method
        for prop_key, _, _ in specs:
            store_original_method(prop_key, original)

        wrapper = _make_combined_wrapper(SymClass, method_name, specs)
        setattr(SymClass, method_name, wrapper)


# Apply patches immediately upon import
apply_all_patches()


# ────────────────────────────────────────────────────────────────────────────────
# Self‐test block (for debugging)
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sympy
    from sympy import Symbol, Limit, Derivative
    from symantex.registry import register_property, register_patch
    from symantex.factory import build_operator_class
    from symantex.mixins.base import PropertyMixin

    # 1) Test pull_limit
    @register_property(
        "test_limit",
        "Example mixin: pull limit inside function."
    )
    class TestLimitMixin(PropertyMixin):
        def _eval_limit(self, var, point, direction):
            orig_doit = getattr(self.func, "__orig_doit", None)
            if orig_doit is None:
                return sympy.Limit(self, var, point, direction)

            inner = sympy.Limit(self.args[0], var, point, direction)
            val = orig_doit(inner)
            return self.func(val)

    # Now use a **callable** for head_attr:
    register_patch(
        "test_limit",
        sympy.Limit,
        "doit",
        "_eval_limit",
        lambda self: self.args[0]   # ← because Limit(expr, …).args[0] is the head
    )
    apply_all_patches()

    x = Symbol("x")
    print("\n=== Running Limit tests ===\n")

    F = build_operator_class("F", ["test_limit"], arity=1)
    G = build_operator_class("G", [], arity=1)

    expr_F = Limit(F(x**2), x, 0, "+")
    result_F = expr_F.doit()
    print(f"\nResult for F w/ test_limit: {result_F}\n")      # → F(0)

    expr_G = Limit(G(x**2), x, 0, "+")
    result_G = expr_G.doit()
    print(f"\nResult for G w/out test_limit: {result_G}\n")   # → Limit(G(x^2), x, 0)

    # 2) Test pull_derivative_chain
    @register_property(
        "test_deriv",
        "Example mixin: pull derivative inside function."
    )
    class TestDerivMixin(PropertyMixin):
        def _eval_derivative(self, var):
            orig_doit = getattr(self.func, "__orig_doit", None)
            if orig_doit is None:
                return sympy.Derivative(self, var)

            inner = sympy.Derivative(self.args[0], var)
            val = orig_doit(inner)
            return self.func(val)

    register_patch(
        "test_deriv",
        sympy.Derivative,
        "doit",
        "_eval_derivative",
        lambda self: self.args[0]   # ← because Derivative(expr, var).args[0] is the head
    )
    apply_all_patches()

    print("\n=== Running Derivative tests ===\n")
    H = build_operator_class("H", ["test_deriv"], arity=1)
    K = build_operator_class("K", [], arity=1)

    expr_H = Derivative(H(x**3), x)
    result_H = expr_H.doit()
    print(f"\nResult for H w/ test_deriv: {result_H}")   # → H(3*x**2)

    expr_K = Derivative(K(x**3), x)
    result_K = expr_K.doit()
    print(f"\nResult for K w/out test_deriv: {result_K}\n")# → Derivative(K(x^3), x)

    print("\nAll generic‐patch tests completed.")
