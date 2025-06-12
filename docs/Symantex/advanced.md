----------------------------------
title: Advanced Topics
description: Advanced Usage with Symantex
slug: /projects/symantex/advanced/
sidebar_position: 3
----------------------------------

# Advanced Topics

## Failure‑mode diagnostics

Set `failure_logs=True` to bundle the full prompt and raw model JSON into any raised `StructuredOutputError` or `SympyConversionError`.

```python
try:
    sx.to_sympy(r"malformed latex $$", failure_logs=True)
except SympyConversionError as err:
    print(err.notes)      # shows prompt + raw LLM answer
```

## Custom locals (registering new symbols/functions)

```python
import sympy as sp
sx.to_sympy("f(x) = 0")                 # f → Function('f') auto‑created

# But you can bind it explicitly:
custom = {"f": sp.Function("f", real=True)}
exprs = sx.to_sympy("f(x)=0", extra_locals=custom)
```

## Switching provider/model

```python
sx = Symantex(provider="openai", model="gpt-4o-mini")   # default
sx.set_model("gpt-4o")    # once you have access to the bigger model
```
