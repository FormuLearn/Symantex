# Symantex

**Symantex** (pronounced “semantics”) is a modular LaTeX→SymPy converter built on top of Mirascope’s structured-JSON API.  It transforms arbitrary LaTeX snippets into executable SymPy `Expr` and `Eq` objects, with hooks for domain-specific operators, custom prompt engineering, and dynamic parser configuration.

**Documentation:** Available at [FormuLearn Docs](https://docs.formulearn.org/docs/projects)

---

## 🚀 Features

- **Reliable JSON mode** via Mirascope LLM calls  
- **Automatic parsing** into SymPy ASTs (`Eq`, `Sum`, `Matrix`, derivatives, transforms…)  
- **Dynamic locals map** lets you register new functions/symbols (e.g. `argmin`, `softmax`, `attention`)  
- **Pluggable prompt** that enforces valid Sympy code (`Eq(...)`, `Sum(...)`, no ellipses)  
- **Graceful degradation**: partial parse success, intelligent failure logging for diagnostics  
- **Customizable parser** via regular-expression token discovery  

---

## 📦 Installation

```bash
pip install symantex
```

## Contributing

To contribute, start by creating and entering a virtual environment (Python 3.10 reccomended)

```bash
python3.10 -m venv .symnatex && source .symantex/bin/activate
```

After that, clone the repository and enter the Symantex folder

```bash
git clone git@github.com:FormuLearn/Symantex.git && cd Symantex
```

You can then install requirements with:

```bash
pip install -r requirements.txt
```

Finally, locally install the library locally with:

```bash
pip install -e .
```

Now any changes you make to the library locally will be reflected in your installation.
