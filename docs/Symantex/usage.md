-------------------------------
title: Basic Usage
description: Basic usage with Symantex
slug: /projects/symantex/usage/
sidebar_position: 2
-------------------------------

# Basic Usage

## Quick reference

```python
sx = Symantex()
sx.register_key(API_KEY)
exprs, notes, multiple = sx.to_sympy(
    latex="A = \\frac{B}{C}",
    output_notes=True,
    failure_logs=False,
)
```

| Parameter      | Purpose                                                  | Default      |
| -------------- | -------------------------------------------------------- | ------------ |
| `latex`        | Raw LaTeX string                                         | **required** |
| `context`      | Extra prose fed to the LLM (units, domain assumptions …) | `None`       |
| `output_notes` | Return the model’s commentary                            | `False`      |
| `failure_logs` | Attach prompt & raw output to any raised error           | `False`      |
| `max_retries`  | Self‑repair rounds the model may attempt                 | `2`          |

### Returning multiple expressions

```python
exprs, _, multiple = sx.to_sympy(r"\begin{cases} x^2+y^2=1, \\ x-y=0 \end{cases}", output_notes=True)
assert multiple and len(exprs) == 2
```

### Providing domain context

```python
sx.to_sympy(
    r"E = m c^2",
    context="Assume c is the speed of light, m is mass.",
)
```

