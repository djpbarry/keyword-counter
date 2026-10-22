import csv
import os
import re

import pymupdf as fitz


def count_keywords_in_pdf(pdf_path, search_terms):
    document = fitz.open(pdf_path)
    keyword_counts = {term: 0 for term, _ in search_terms}

    # Compile one regex per term: stems match whole words sharing the
    # prefix; whole words match the word exactly.
    patterns = {
        term: re.compile(
            rf"\b{re.escape(term.lower())}\w*"
            if kind == "stem"
            else rf"\b{re.escape(term.lower())}\b"
        )
        for term, kind in search_terms
    }

    # Loop through each page in the PDF
    for page in document:
        text = page.get_text("text")  # Extract the text from the page
        if text:
            text = text.lower()  # Convert the page text to lowercase
            for term, _ in search_terms:
                # Count whole-word occurrences (case-insensitive)
                keyword_counts[term] += len(patterns[term].findall(text))

    document.close()
    return keyword_counts


def analyze_folder(folder_path, search_terms, output_csv):
    term_names = [term for term, _ in search_terms]
    # Prepare the CSV file to store the results
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row: filename + search terms
        writer.writerow(['filename'] + term_names)

        # Loop through all PDF files in the folder
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                # Count the keywords in the PDF
                keyword_counts = count_keywords_in_pdf(pdf_path, search_terms)
                # Write the results for the current PDF file to the CSV
                row = [filename] + [keyword_counts[term] for term in term_names]
                writer.writerow(row)


# Example usage
folder_path = "D:/OneDrive - The Francis Crick Institute/Sandwich Students/2027/CVs"  # Folder containing PDF files
# Search terms as (term, kind) pairs. kind is "stem" (match any whole word
# starting with the term) or "word" (match the whole word exactly). Order
# determines the CSV column order.
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
    ('imag', 'stem'),
]
output_csv = "keyword_counts.csv"

analyze_folder(folder_path, search_terms, output_csv)
