# File: symantex/patches.py

import sympy
from sympy import Limit as _OrigLimit

# Keep a reference to the original Limit.doit
_orig_limit_doit = _OrigLimit.doit

def _monkeypatched_limit_doit(self, **hints): # Allows for an _eval_limit method to mixins for limits. Allows for similar logic to mixins for derivatives/integrals
    """
    Wrapper for Limit.doit that first checks if the integrand’s head
    defines _eval_limit. If so, calls that; otherwise falls back.
    """
    expr, var, point, dir = self.args
    try:
        head = expr.func
        if hasattr(head, "_eval_limit"):
            return expr._eval_limit(var, point, dir, **hints)
    except Exception:
        pass
    return _orig_limit_doit(self, **hints)

_OrigLimit.doit = _monkeypatched_limit_doit
