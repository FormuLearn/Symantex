# File: symantex/_patches.py

import functools
import sympy
from typing import Dict, List, Tuple, Type, Union, Callable, Optional
from symantex.registry import all_patch_specs, store_original_method, get_original_method

# ────────────────────────────────────────────────────────────────────────────────
# We rebuild this mapping on each call to apply_all_patches().
# It maps (SymClass, method_name) → list of (property_key, hook_name, head_attr, arg_extractor).
#
# head_attr can be either:
#   - a string (the attribute name on `self`), or
#   - a callable `f(self) → Expression` that extracts the “head”
#
# arg_extractor can be:
#   - a callable `f(self) → tuple` of positional arguments for the hook, or
#   - `None`, in which case we fall back to SymPy‐specific defaults (e.g. Derivative, Limit, Integral).
# ────────────────────────────────────────────────────────────────────────────────

# (Reconstructed in apply_all_patches)
# Mapping: (SymClass, method_name) → List[ (prop_key, hook_name, head_attr, arg_extractor) ]
_METHOD_PATCHES: Dict[
    Tuple[Type, str],
    List[Tuple[str, str, Union[str, Callable], Optional[Callable]]]
] = {}


def _build_method_patches():
    """
    Reconstruct `_METHOD_PATCHES` from the current `all_patch_specs()`.
    Each entry from all_patch_specs() is now:
      (property_key, SymClass, method_name, hook_name, head_attr, arg_extractor)
    """
    global _METHOD_PATCHES
    _METHOD_PATCHES = {}
    for prop_key, SymClass, method_name, hook_name, head_attr, arg_extractor in all_patch_specs():
        key = (SymClass, method_name)
        _METHOD_PATCHES.setdefault(key, []).append(
            (prop_key, hook_name, head_attr, arg_extractor)
        )


def _make_combined_wrapper(
    SymClass: Type,
    method_name: str,
    specs: List[Tuple[str, str, Union[str, Callable], Optional[Callable]]]
):
    """
    Create a single wrapper for `SymClass.method_name` that checks
    all registered (property_key, hook_name, head_attr, arg_extractor) in order.
    """

    original_method = getattr(SymClass, method_name)

    @functools.wraps(original_method)
    def patched(self, *args, **kwargs):
        # 1) Attempt to extract “head” (the inner operator/function) via head_attr.
        head: Optional[sympy.Basic] = None
        for _, _, head_attr, _ in specs:
            if isinstance(head_attr, str):
                if hasattr(self, head_attr):
                    head = getattr(self, head_attr)
                    break
            else:
                # assume head_attr is a callable(self) -> Expression
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

        # 4) Try each patch spec in registration order
        for prop_key, hook_name, head_attr, arg_extractor in specs:
            if prop_key in prop_keys:
                # Found a matching property_key
                # Re‐extract the “head2” exactly the same way
                if isinstance(head_attr, str):
                    head2 = getattr(self, head_attr, None)
                else:
                    head2 = head_attr(self)

                # The mixin’s hook lives on head2.func
                hook = getattr(head2.func, hook_name, None)
                if hook is None:
                    # this mixin didn’t define that particular _eval_* hook
                    continue

                # Attach the original unpatched method under "__orig_<method_name>"
                try:
                    orig = get_original_method(prop_key)
                    setattr(head2.func, f"__orig_{method_name}", orig)
                except KeyError:
                    pass

                # 5) Build `hook_args`:
                #    - If arg_extractor was provided, obey it.
                #    - Otherwise, fall back to SymPy‐specific logic for Derivative, Limit, Integral.
                if arg_extractor is not None:
                    hook_args = arg_extractor(self) or ()
                else:
                    # Default fallback:
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

        # 6) if head.func has ANY `property_keys` attribute (even empty list), treat
        #    it as “custom” and return unevaluated
        if hasattr(head, "func") and hasattr(head.func, "property_keys"):
            return self


        # 7) Otherwise, no custom patch applies → call the original method
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
        # 2) Save the original (unpatched) method under each prop_key so that
        #    mixins can call get_original_method(prop_key) if needed.
        from symantex.registry import store_original_method
        for prop_key, _, _, _ in specs:
            store_original_method(prop_key, original)

        # 3) Build and install a single wrapper that checks all registered specs in order.
        wrapper = _make_combined_wrapper(SymClass, method_name, specs)
        setattr(SymClass, method_name, wrapper)


# Apply patches immediately when this module is imported
apply_all_patches()


# ────────────────────────────────────────────────────────────────────────────────
# Self‐test block (for debugging)
# ────────────────────────────────────────────────────────────────────────────────
# File: symantex/_patches.py
# ────────────────────────────────────────────────────────────────────────────────
# (… the imports and _make_combined_wrapper / apply_all_patches code remain unchanged …)
# ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sympy
    from sympy import Symbol, Limit, Derivative
    from symantex.registry import register_property, register_patch
    from symantex.factory import build_operator_class
    from symantex.mixins.base import PropertyMixin

    # ────────────────────────────────────────────────────────────────────────────
    # 1) Test pull_limit
    # ────────────────────────────────────────────────────────────────────────────
    @register_property(
        "test_limit",
        "Example mixin: pull limit inside function."
    )
    class TestLimitMixin(PropertyMixin):
        def _eval_limit(self, var, point, direction):
            orig_doit = getattr(self.func, "__orig_doit", None)
            if orig_doit is None:
                # fallback: unevaluated Limit
                return sympy.Limit(self, var, point, direction)

            # extract inner payload from _args or _nargs
            try:
                inner_payload = self._args[0]
            except AttributeError:
                inner_payload = self._nargs[0]

            # build a Limit around that payload, call the original .doit(), then re-wrap
            inner = sympy.Limit(inner_payload, var, point, direction)
            val = orig_doit(inner)
            return self.func(val)

    # Register patch spec for Limit.doit:
    #   head_attr    = lambda self: (the “wrapped operator” inside Limit)
    #   arg_extractor = (var, point, direction) from _args or _nargs
    register_patch(
        "test_limit",
        sympy.Limit,
        "doit",
        "_eval_limit",
        head_attr=lambda self: (self._args[0] if hasattr(self, "_args") else self._nargs[0]),
        arg_extractor=lambda self: (
            (self.args[1] if hasattr(self, "_args") else self._nargs[1]),
            (self.args[2] if hasattr(self, "_args") else self._nargs[2]),
            (self.args[3] if hasattr(self, "_args") else self._nargs[3])
        )
    )

    # Re‐apply patches
    from symantex._patches import apply_all_patches
    apply_all_patches()

    x = Symbol("x")
    print("\n=== Running Limit tests ===\n")

    F = build_operator_class("F", ["test_limit"], arity=1)
    G = build_operator_class("G", [], arity=1)

    expr_F = Limit(F(x**2), x, 0, "+")
    result_F = expr_F.doit()
    # Use str(...) to avoid accessing result_F.args during formatting
    print("Result for F w/ test_limit:", str(result_F))  # → F(0)

    expr_G = Limit(G(x**2), x, 0, "+")
    result_G = expr_G.doit()
    print("Result for G w/out test_limit:", str(result_G))  # → Limit(G(x^2), x, 0)

    # ────────────────────────────────────────────────────────────────────────────
    # 2) Test pull_derivative_chain
    # ────────────────────────────────────────────────────────────────────────────
    @register_property(
        "test_deriv",
        "Example mixin: pull derivative inside function."
    )
    class TestDerivMixin(PropertyMixin):
        def _eval_derivative(self, var):
            orig_doit = getattr(self.func, "__orig_doit", None)
            if orig_doit is None:
                # fallback: unevaluated Derivative
                return sympy.Derivative(self, var)

            # extract inner payload from _args or _nargs
            try:
                inner_payload = self._args[0]
            except AttributeError:
                inner_payload = self._nargs[0]

            # form Derivative(inner_payload, var), call original .doit(), then re-wrap
            inner = sympy.Derivative(inner_payload, var)
            val = orig_doit(inner)
            return self.func(val)

    # Register patch spec for Derivative.doit:
    #   head_attr    = lambda self: (the operator inside Derivative)
    #   arg_extractor = (the differentiation variable) = self._args[1] or _nargs[1]
    register_patch(
        "test_deriv",
        sympy.Derivative,
        "doit",
        "_eval_derivative",
        head_attr=lambda self: (self._args[0] if hasattr(self, "_args") else self._nargs[0]),
        arg_extractor=lambda self: ((self._args[1] if hasattr(self, "_args") else self._nargs[1]),)
    )

    # Re‐apply patches
    apply_all_patches()

    print("\n=== Running Derivative tests ===\n")
    H = build_operator_class("H", ["test_deriv"], arity=1)
    K = build_operator_class("K", [], arity=1)

    expr_H = Derivative(H(x**3), x)
    result_H = expr_H.doit()
    print("Result for H w/ test_deriv:", str(result_H))  # → H(3*x**2)

    expr_K = Derivative(K(x**3), x)
    result_K = expr_K.doit()
    print("Result for K w/out test_deriv:", str(result_K))  # → Derivative(K(x^3), x)

    print("\nAll generic-patch tests completed.")
