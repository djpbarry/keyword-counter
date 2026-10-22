import csv
import math
import os
import re
import sys

import pymupdf as fitz


def normalize_text(text):
    # Join words split across lines by a hyphen (e.g. "micro-\nscope").
    text = re.sub(r"-\s*\n\s*", "", text)
    # Collapse all whitespace (including PDF line breaks) to single spaces.
    text = re.sub(r"\s+", " ", text)
    # Expand common typographic ligatures to their ASCII equivalents.
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    return text


def count_keywords_in_pdf(pdf_path, search_terms):
    document = fitz.open(pdf_path)
    keyword_counts = {term: 0 for term, _ in search_terms}
    total_words = 0

    # Compile one regex per term. "stem" terms match any whole word with the
    # term as a prefix; "word" and "phrase" terms match exactly (phrases may
    # contain spaces, which normalization has collapsed to single spaces).
    patterns = {}
    for term, kind in search_terms:
        escaped = re.escape(term.lower())
        if kind == "stem":
            patterns[term] = re.compile(rf"\b{escaped}\w*")
        else:
            patterns[term] = re.compile(rf"\b{escaped}\b")

    # Loop through each page in the PDF
    for page in document:
        text = page.get_text("text")  # Extract the text from the page
        if text:
            # Lowercase and normalize before matching
            text = normalize_text(text.lower())
            total_words += len(text.split())  # Tally words for density
            for term, _ in search_terms:
                # Count whole-word occurrences (case-insensitive)
                keyword_counts[term] += len(patterns[term].findall(text))

    document.close()
    return keyword_counts, total_words


def analyze_folder(folder_path, search_terms, output_csv):
    term_names = [term for term, _ in search_terms]
    results = []  # (filename, status, keyword_counts, total_words)

    # First pass: process every PDF, collecting counts and flagging
    # unreadable (no text) or error (corrupt/encrypted) files.
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            try:
                keyword_counts, total_words = count_keywords_in_pdf(pdf_path, search_terms)
                status = 'unreadable' if total_words == 0 else 'ok'
                results.append((filename, status, keyword_counts, total_words))
            except Exception as exc:
                print(f"Skipping {filename}: {exc}", file=sys.stderr)
                results.append((filename, 'error', {term: 0 for term in term_names}, 0))

    # Compute rarity weights from document frequency across readable files.
    # A term mentioned by few CVs is more informative when present.
    readable = [r for r in results if r[1] == 'ok']
    n_docs = len(readable)
    doc_freq = {term: sum(1 for _, _, counts, _ in readable if counts[term] > 0) for term in term_names}
    weights = {
        term: (1.0 + math.log10(n_docs / doc_freq[term])) if doc_freq[term] > 0 else 1.0
        for term in term_names
    }

    # Prepare the CSV file to store the results
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Header: filename, status, total word count, binary score, weighted
        # score, then for each term a raw count, a 0/1 "mentioned" flag, and
        # a density (count / total words).
        header = ['filename', 'status', 'total_words', 'score', 'weighted_score']
        for term in term_names:
            header += [term, term + '_mentioned', term + '_density']
        writer.writerow(header)

        for filename, status, counts, total_words in results:
            if status == 'ok':
                score = sum(1 for term in term_names if counts[term] > 0)
                weighted = round(sum(weights[term] for term in term_names if counts[term] > 0), 3)
            else:
                score = 0
                weighted = 0.0
            row = [filename, status, total_words, score, weighted]
            for term in term_names:
                count = counts[term]
                row += [
                    count,
                    1 if count else 0,
                    round(count / total_words, 6) if total_words else 0.0,
                ]
            writer.writerow(row)


# Example usage
folder_path = "D:/OneDrive - The Francis Crick Institute/Sandwich Students/2027/CVs"  # Folder containing PDF files
# Search terms as (term, kind) pairs. kind is "stem" (match any whole word
# starting with the term), "word" (match the whole word exactly), or
# "phrase" (match a multi-word phrase exactly). Order determines the CSV
# column order.
search_terms = [
    ('FIJI', 'word'),
    ('CellProfiler', 'word'),
    ('Cell Profiler', 'phrase'),
    ('ImageJ', 'word'),
    ('OpenCV', 'word'),
    ('QuPath', 'word'),
    ('napari', 'word'),
    ('Ilastik', 'word'),
    ('Imaris', 'word'),
    ('skimage', 'word'),
    ('StarDist', 'word'),
    ('microscop', 'stem'),
    ('python', 'word'),
    ('matlab', 'word'),
    ('code', 'word'),
    ('coding', 'word'),
    ('git', 'stem'),
    ('docker', 'word'),
    ('script', 'word'),
    ('segmentation', 'word'),
    ('comput', 'stem'),
    ('model', 'word'),
    ('fluoresc', 'stem'),
    ('slide', 'word'),
    ('rstudio', 'word'),
    ('graphpad', 'word'),
    ('prism', 'word'),
    ('statistic', 'stem'),
    ('programming', 'word'),
    ('machine learning', 'phrase'),
    ('deep learning', 'phrase'),
    ('neural network', 'phrase'),
    ('imag', 'stem'),
]
output_csv = "keyword_counts.csv"

analyze_folder(folder_path, search_terms, output_csv)
