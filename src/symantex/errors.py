#symantex/errors.py

class SymantexError(Exception):
    """Base class for all Symantex errors."""

class APIKeyMissingError(SymantexError):
    """Raised when register_key() wasn’t called before to_sympy()."""

class UnsupportedModelError(SymantexError):
    """Raised at init if the chosen model isn’t known to support JSON mode."""

class UnsupportedProviderError(SymantexError):
    """Raised at init if the LLM provider is unknown"""

class StructuredOutputError(SymantexError):
    """
    Raised when the LLM fails to produce valid JSON.
    .notes will contain the raw error or model message.
    """

class EmptyExpressionsError(SymantexError):
    """Raised when the parsed JSON has an empty `exprs` list."""

class SympyConversionError(SymantexError):
    """
    Raised when sympy.sympify() fails on a returned expression string.
    .expr_str will hold the offending snippet.
    .notes may include the LLM’s original notes.
    """
