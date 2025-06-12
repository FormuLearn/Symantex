-------------------------
title: Symantex
description: High‑level overview of the Symantex library – LaTeX ➜ SymPy via LLMs
slug: projects/symantex/
-------------------------

# Symantex

**Symantex** turns raw LaTeX into ready‑to‑use [SymPy](https://www.sympy.org/) expressions by delegating the heavy lifting to a JSON‑mode LLM (OpenAI GPT‑4o‑mini by default).  It ships a thin Python facade that:

* builds a concise, example‑driven prompt;
* validates the LLM’s JSON and re‑prompts for self‑repair when needed; and
* hands back *real* `sympy.Expr` objects – no brittle text post‑processing.

---

## Key features

| Feature                          | What it gives you                                                       |
| -------------------------------- | ----------------------------------------------------------------------- |
| **One‑line install**             | `pip install symantex`                                                  |
| **Strict JSON contract**         | deterministic parsing – if the model drifts, it fixes itself            |
| **Automatic function discovery** | unknown calls like `relu(x)` are promoted to `Function('relu')`         |
| **Ambiguous symbol handling**    | `N`, `E`, `I`, `pi` are safe – Symbol vs. Function decided contextually |
| **Failure logs switch**          | one flag to surface raw prompt / model output for debugging             |
| **Extensible locals**            | register your own operators or constants in a single call               |

---

## Project structure (docs excerpt)

```
docs/
└─ Symantex/
   ├─ index.md          ← this page
   ├─ getting-started.md
   ├─ usage.md
   ├─ advanced.md
   ├─ troubleshooting.md
   └─ mixins.md
```

> 📖  Continue with **Getting Started** for a 30‑second install & first round‑trip.
