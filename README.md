# PDF Alchemy

This is the template repo for the CLI tool to manipulate pdfs

**Fork** the project to your github account, this will have the assotiated tests and template to start the project and finish implementation

# Requirements
- Python
- UV
- pymupdf

# Sync and update project packages

```bash
uv sync
```

# Run the tool

1. Initialize `venv`
```bash
uv venv
```

```bash
source .venv/bin/activate
```

2. Run the tool
```bash
uv run main.py
```

# Commands

> Add here the commands
# resumen de textos 
uv run main.py -f ./tests/assets/test_alchemy.pdf -o ./out/resumen.txt summarize

# traductor 
uv run main.py -f ./tests/assets/test_alchemy.pdf -o ./out/traducido.txt translate --target-lang en

# Run tests

```bash
uv run pytest -q
```

# Compile to a standalone executable

```bash
uv pip install pyinstaller
```

```bash
uv run pyinstaller --onefile main.py
```

> You'll see the new compilation under `dist/`
