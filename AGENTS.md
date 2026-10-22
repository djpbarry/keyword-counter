# AGENTS.md

## Project overview

A small, single-purpose utility that scans a folder of PDF files (job
applications / CVs) and counts how many times each of a list of keywords
appears, writing the results to a CSV.

Despite the filename, `highlight_pdf.py` does **not** highlight anything.
It extracts text from PDFs and counts keyword occurrences.

There is no package structure, no test suite, no linter config, and no CI.
The entire program is one script.

## Tech stack and environment

- **Pixi** (`pixi.toml`) manages the Python environment.
  - Channel: `conda-forge`
  - Platforms: `win-64` only (Windows-specific; hardcoded paths in the
    script are Windows drive-letter paths)
  - Python `>=3.15.0,<3.16` (very new — some packages may lack wheels)
- **PyMuPDF** is the PDF library. Imported as `import pymupdf as fitz`
  (the `fitz` module is the legacy alias).
- Declared dependencies in `pixi.toml`:
  - `[dependencies]`: `python`, `pixi-pycharm`
  - `[pypi-dependencies]`: `pymupdf`
- Two environments exist: `default` and `scanner`
  (`[environments] scanner = ["default"]`).

## Commands

There are no Pixi tasks defined (`[tasks]` is empty) and no Makefile,
`package.json`, or CI workflows, so there is no build/test/lint entrypoint.

Environment management (Pixi):

```sh
pixi install        # (re)install/update environments and regenerate pixi.lock
pixi shell -e scanner
```

Running the script inside the Pixi environment:

```sh
pixi run -e scanner python highlight_pdf.py
```

Use the `scanner` environment, not `default`: `pymupdf`/`fitz` is installed
in `.pixi/envs/scanner`, not in `.pixi/envs/default`. Running against
`default` fails with `ModuleNotFoundError: No module named 'pymupdf'`.

## Code organization

`highlight_pdf.py` is the only source file. Data flow:

1. `analyze_folder(folder_path, search_terms, output_csv)` opens the output
   CSV, writes a header row, then iterates over every `*.pdf` in the folder.
2. For each PDF, `count_keywords_in_pdf(pdf_path, search_terms)` opens it
   with `fitz`, extracts `page.get_text("text")` per page, and feeds each
   page through `normalize_text` (joins hyphenated line breaks, collapses
   whitespace, expands ligatures) before lowercasing.
3. Each term is matched with a compiled regex built from its kind: `stem`
   terms use `\bterm\w*`, `word` and `phrase` terms use `\bterm\b` (phrases
   may contain spaces, already collapsed by normalization). The function
   returns `(keyword_counts, total_words)`.
4. `analyze_folder` writes one row per file: `filename`, a `status`
   (`ok` / `unreadable` / `error`), `total_words`, and per term a raw
   `count`, a `0/1` `*_mentioned` flag, and a `*_density`
   (`count / total_words`).

## Gotchas (non-obvious)

- **Hardcoded config at the bottom of the script.** `folder_path`,
  `search_terms`, and `output_csv` are literal values in module scope
  (`highlight_pdf.py:56-85`), not CLI args or a config file. `folder_path`
  is an absolute OneDrive path that must exist on the machine running the
  script. To change inputs/outputs, edit these values directly.
- **Stem vs word vs phrase matching is explicit.** `search_terms` is a list
  of `(term, kind)` tuples where `kind` is `"stem"`, `"word"`, or `"phrase"`
  (`highlight_pdf.py:86`). Stems match any whole word starting with the term
  (`\bterm\w*`); words and phrases match exactly (`\bterm\b`). This means
  plurals and other suffixes are NOT matched for `word` terms: e.g. `script`
  will not match "scripts", `analysis` will not match "analyses".
- **Stale lockfile.** `pixi.lock` is currently untracked and does not yet
  reflect the `pymupdf` addition (no `pymupdf` entry). Run `pixi install`
  or `pixi update` to regenerate it after dependency changes.
- **`.idea/` is untracked and not ignored.** `.gitignore` only ignores
  `.pixi/*` (except `config.toml`). PyCharm project files may show up as
  untracked; don't commit them.
- **Unreadable and corrupt PDFs are flagged, not fatal.** PDFs with no
  extractable text (likely scanned images) get `status = unreadable`; corrupt
  or encrypted PDFs get `status = error` and are logged to stderr. The batch
  continues past both.
- **No `pymupdf`/`fitz` in `default` env** — always target `scanner` (see
  Commands).
- The script has no `if __name__ == "__main__"` guard; importing it runs the
  analysis immediately.

## Conventions

- Plain procedural Python: `csv`, `os`, and `re` from the standard library
  plus `pymupdf as fitz` (PyMuPDF). No type hints, no docstrings beyond a few
  inline comments.
- Existing style keeps all logic in module-level functions with the
  invocation at the bottom; follow that pattern if extending, but consider
  adding an entrypoint guard and CLI/`argparse` if the script grows.

## Improvement backlog

Planned keyword-detection improvements (regex word boundaries, term
normalization, OCR, etc.) are tracked in `DEVELOPMENT_NOTES.md`. Read that
before touching the matching logic.
