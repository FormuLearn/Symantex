-----------------------------------------
title: Troubleshooting
description: Troubleshooting Symantex
slug: /projects/symantex/troubleshooting/
sidebar_position: 4
-----------------------------------------

# Troubleshooting

| Symantex error          | Typical cause                           | Quick fix                                     |
| ----------------------- | --------------------------------------- | --------------------------------------------- |
| `APIKeyMissingError`    | `register_key` never called             | `sx.register_key(key)`                        |
| `StructuredOutputError` | LLM produced bad JSON / server envelope | retry; inspect `err` with `failure_logs=True` |
| `EmptyExpressionsError` | JSON had no `exprs`                     | tighten your LaTeX or add context             |
| `SympyConversionError`  | Returned strings weren’t valid SymPy    | file an issue with the failing LaTeX          |

If retries fail, open an issue and paste the **prompt** + **raw model output** (visible when `failure_logs=True`).
