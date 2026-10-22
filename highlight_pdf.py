import csv
import os
import re

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
    # Prepare the CSV file to store the results
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row: filename, total word count, then for each
        # term a raw count, a 0/1 "mentioned" flag, and a density (count /
        # total words) so results can be compared across CVs of different
        # lengths.
        header = ['filename', 'total_words']
        for term in term_names:
            header += [term, term + '_mentioned', term + '_density']
        writer.writerow(header)

        # Loop through all PDF files in the folder
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                # Count the keywords in the PDF
                keyword_counts, total_words = count_keywords_in_pdf(pdf_path, search_terms)
                # Write the results for the current PDF file to the CSV
                row = [filename, total_words]
                for term in term_names:
                    count = keyword_counts[term]
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
    ('cell', 'word'),
    ('FIJI', 'word'),
    ('CellProfiler', 'word'),
    ('microscop', 'stem'),
    ('python', 'word'),
    ('matlab', 'word'),
    ('code', 'word'),
    ('coding', 'word'),
    ('script', 'word'),
    ('data', 'word'),
    ('analysis', 'word'),
    ('comput', 'stem'),
    ('model', 'word'),
    ('fluoresc', 'stem'),
    ('slide', 'word'),
    ('rstudio', 'word'),
    ('graphpad', 'word'),
    ('prism', 'word'),
    ('statistic', 'stem'),
    ('program', 'stem'),
    ('machine', 'word'),
    ('learning', 'word'),
    ('machine learning', 'phrase'),
    ('imag', 'stem'),
]
output_csv = "keyword_counts.csv"

analyze_folder(folder_path, search_terms, output_csv)
