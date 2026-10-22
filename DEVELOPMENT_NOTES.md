# Development Notes

Ideas and improvements for `highlight_pdf.py`, focused on keyword detection.

## Core problem

`count_keywords_in_pdf` uses `text.count(term)` (`highlight_pdf.py:17`), which
is raw substring matching with no word boundaries. This inflates counts
badly. Examples from the current term list:

- `imag` → "image", "imaging", "imagine", "imagination"
- `cell` → "Excel", "cellphone", "cellular"
- `code` → "encode", "postcode", "barcode"
- `script` → "description", "subscription", "JavaScript"
- `data` → "database", "metadata", "dataframe"
- `slide` → "slides", "landslide"

## Improvements (by impact)

1. **Word-boundary matching (biggest win).** Use regex instead of `.count()`:

   ```python
   import re

   def count_keywords_in_pdf(pdf_path, search_terms):
       document = fitz.open(pdf_path)
       counts = {term: 0 for term in search_terms}
       for page in document:
           text = page.get_text("text").lower()
           for term in search_terms:
               counts[term] += len(re.findall(rf"\b{re.escape(term)}\b", text))
       document.close()
       return counts
   ```

   `\b` does not work for stems (`microscop`, `imag`, `fluoresc`) because the
   boundary would have to fall immediately after the stem. Use a word-prefix
   pattern for stems:

   ```python
   pattern = rf"\b{re.escape(term)}\w*" if term_is_stem else rf"\b{re.escape(term)}\b"
   ```

2. **Make the term list consistent.** The list mixes stems (`microscop`,
   `comput`, `statistic`) with full words (`cell`, `code`, `python`). Decide
   one form and encode it explicitly (e.g. a list of `(term, "stem"|"word")`
   tuples) so the matcher knows whether to allow a suffix.

3. **Normalize text before matching.** `get_text("text")` inserts newlines at
   line breaks, so "micro-\nscope" or "cell\nprofiler" won't match. Collapse
   whitespace and normalize hyphenation and ligatures first:

   ```python
   text = re.sub(r"-\s*\n\s*", "", text)   # join hyphenated line breaks
   text = re.sub(r"\s+", " ", text)
   text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
   ```

4. **Decide presence vs frequency.** Raw counts are skewed by CV length.
   Consider writing both a binary "mentioned" column and a density
   (`count / total_words`) to rank meaningfully across documents.

5. **Support phrases.** `machine learning` is currently counted as `machine`
   + `learning` separately. Keep phrases as single terms and match
   `\bmachine learning\b` after whitespace normalization.

6. **OCR for scanned PDFs.** `get_text("text")` returns empty for image-only
   PDFs (common with scanned CVs). Detect empty pages and fall back to
   rendering the page to an image via `fitz` + `pytesseract`.

7. **Error handling.** Wrap each file in `try/except` so one corrupt or
   encrypted PDF doesn't abort the whole batch; skip and log the filename.

## Status

- [x] Item 1 (regex word boundaries) implemented in
      `highlight_pdf.py:count_keywords_in_pdf`: stems use `\bterm\w*`,
      everything else uses `\bterm\b`.
- [x] Item 2 (consistent term encoding) implemented: `search_terms` is now a
      list of `(term, kind)` tuples with `kind` in `{"stem", "word"}`
      (`highlight_pdf.py:60`). The kind is read in `count_keywords_in_pdf`
      and `analyze_folder`; the separate `STEM_TERMS` set was removed.
- [ ] Items 3–7 remain open. A sensible next increment is item 3 (text
      normalization) plus item 4 (presence vs frequency).
