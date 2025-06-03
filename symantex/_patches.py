# File: symantex/_patches.py

import functools
import sympy
from typing import Callable
from symantex.registry import all_patch_specs, get_original_method

# ────────────────────────────────────────────────────────────────────────────────
# Generic wrapper factory (with debug prints)
# ────────────────────────────────────────────────────────────────────────────────
def _make_wrapper(key: str,
                  SymClass: type,
                  method_name: str,
                  hook_name: str,
                  head_extractor: Callable,
                  arg_extractor: Callable):
    """
    Return a wrapper that replaces SymClass.method_name.

    - key:            the property_key to check (instance or class).
    - SymClass:       the Sympy class whose method is being overridden.
    - method_name:    name of the method on SymClass (e.g. "doit").
    - hook_name:      name of the mixin method to call (e.g. "_eval_limit").
    - head_extractor: callable f(self) → head expression.
    - arg_extractor:  callable f(self) → tuple of arguments to pass to the hook
                      after the head.
    """
    original_method = getattr(SymClass, method_name)

    @functools.wraps(original_method)
    def patched(self, *args, **kwargs):
        # 1) Extract the head using head_extractor
        head = head_extractor(self)

        # 2) Gather property keys from instance or class
        keys = []
        if head is not None:
            if hasattr(head, "property_keys"):
                keys = getattr(head, "property_keys", [])
            elif hasattr(head, "func") and hasattr(head.func, "property_keys"):
                keys = getattr(head.func, "property_keys", [])

        # Debug print
        print(f"[PATCH-{key}] Called {SymClass.__name__}.{method_name} → head={head}, property_keys={keys}")

        # 3) If key is present, invoke the mixin hook
        if head is not None and key in keys:
            hook = getattr(head.func, hook_name, None)
            if hook is not None:
                # Attach the original (unpatched) method to head.func, so mixins can call it:
                try:
                    orig = get_original_method(key)
                    setattr(head.func, f"__orig_{method_name}", orig)
                except KeyError:
                    # If no original is registered, do nothing
                    pass

                hook_args = arg_extractor(self)
                print(f"[PATCH-{key}] Key found; calling hook {hook_name} with args={hook_args}")
                return hook(head, *hook_args, **kwargs)
            else:
                print(f"[PATCH-{key}] Hook {hook_name} not found on {head.func}")

        # 4) Key not present or hook missing → return self unevaluated
        print(f"[PATCH-{key}] Key not in property_keys; returning self unevaluated\n")
        return self

    return patched


# ────────────────────────────────────────────────────────────────────────────────
# Install all registered patches at import time
# ────────────────────────────────────────────────────────────────────────────────
def apply_all_patches():
    """
    Iterate over all registered patch specs and install each wrapper.
    After this is called, Sympy methods only perform custom behavior
    if head.property_keys (instance or class) contains the corresponding key;
    otherwise, the node is returned unevaluated.
    """
    for (
        key,
        SymClass,
        method_name,
        hook_name,
        head_extractor,
        arg_extractor
    ) in all_patch_specs():
        if hasattr(SymClass, method_name):
            wrapper = _make_wrapper(
                key, SymClass, method_name, hook_name, head_extractor, arg_extractor
            )
            setattr(SymClass, method_name, wrapper)


# Execute patching immediately upon import
apply_all_patches()


# ────────────────────────────────────────────────────────────────────────────────
# Self‐test block to verify the generic patch system (with extra prints)
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sympy
    from sympy import Symbol, Limit, Derivative
    from symantex.registry import register_property, register_patch, get_original_method
    from symantex.factory import build_operator_class
    from symantex.mixins.base import PropertyMixin

    # --------------------------------------
    # 1) Test case for pull_limit
    # --------------------------------------
    @register_property(
        "test_limit",
        "Example mixin: pull limit inside function."
    )
    class TestLimitMixin(PropertyMixin):
        def _eval_limit(self, var, point, direction):
            # Retrieve the unpatched Limit.doit from the registry
            orig_doit = getattr(self.func, "__orig_doit", None)
            if orig_doit is None:
                # As a fallback—if the registry somehow didn’t store one—fetch it directly:
                orig_doit = get_original_method("test_limit")

            # Build a fresh Limit node on the inner expression
            inner_node = sympy.Limit(self.args[0], var, point, direction)
            # Invoke the original method so that x**2 → 0, not an unevaluated Limit
            inner_val = orig_doit(inner_node)
            return self.func(inner_val)

    # Register patch spec for Limit.doit:
    # head_extractor:  lambda self: self.args[0]       (the function inside Limit)
    # arg_extractor:   lambda self: (var, point, dir)  from self.args[1..3]
    register_patch(
        "test_limit",
        sympy.Limit,
        "doit",
        "_eval_limit",
        lambda self: self.args[0],
        lambda self: (self.args[1], self.args[2], self.args[3])
    )

    # Re‐apply patches so our new entry takes effect
    apply_all_patches()

    x = Symbol("x")
    print("\n=== Running Limit tests ===\n")

    F = build_operator_class("F", ["test_limit"], arity=1)
    G = build_operator_class("G", [], arity=1)

    expr_F = Limit(F(x**2), x, 0, "+")
    result_F = expr_F.doit()
    print(f"Result for F with test_limit: {result_F}\n")  # → F(0)

    expr_G = Limit(G(x**2), x, 0, "+")
    result_G = expr_G.doit()
    print(f"Result for G without test_limit: {result_G}\n")  # → Limit(G(x**2), x, 0)

    # --------------------------------------
    # 2) Test case for pull_derivative_chain
    # --------------------------------------
    @register_property(
        "test_deriv",
        "Example mixin: pull derivative inside function."
    )
    class TestDerivMixin(PropertyMixin):
        def _eval_derivative(self, var):
            # Retrieve the unpatched Derivative.doit from registry
            orig_doit = getattr(self.func, "__orig_doit", None)
            if orig_doit is None:
                orig_doit = get_original_method("test_deriv")

            inner_node = sympy.Derivative(self.args[0], var)
            inner_val = orig_doit(inner_node)
            return self.func(inner_val)

    # Register patch spec for Derivative.doit:
    # head_extractor:  lambda self: self.args[0]
    # arg_extractor:   lambda self: (var,)
    register_patch(
        "test_deriv",
        sympy.Derivative,
        "doit",
        "_eval_derivative",
        lambda self: self.args[0],
        lambda self: (self.args[1],)
    )

    # Re‐apply patches so our new entry takes effect
    apply_all_patches()

    print("\n=== Running Derivative tests ===\n")
    H = build_operator_class("H", ["test_deriv"], arity=1)
    K = build_operator_class("K", [], arity=1)

    expr_H = Derivative(H(x**3), x)
    result_H = expr_H.doit()
    print(f"Result for H with test_deriv: {result_H}\n")  # → H(3*x**2)

    expr_K = Derivative(K(x**3), x)
    result_K = expr_K.doit()
    print(f"Result for K without test_deriv: {result_K}\n")  # → Derivative(K(x**3), x)

    print("All generic‐patch tests completed.")
