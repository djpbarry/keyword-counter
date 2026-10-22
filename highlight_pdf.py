import csv
import os
import re

import fitz  # PyMuPDF


# Search terms that are stems (prefixes) rather than complete words. These
# match any whole word beginning with the stem (e.g. "microscop" matches
# "microscope" and "microscopy"). All other terms match whole words exactly.
STEM_TERMS = {"microscop", "comput", "fluoresc", "statistic", "program", "imag"}


def count_keywords_in_pdf(pdf_path, search_terms):
    document = fitz.open(pdf_path)
    keyword_counts = {term: 0 for term in search_terms}

    # Compile one regex per term: stems match whole words sharing the
    # prefix; all other terms match the whole word exactly.
    patterns = {
        term: re.compile(
            rf"\b{re.escape(term.lower())}\w*"
            if term.lower() in STEM_TERMS
            else rf"\b{re.escape(term.lower())}\b"
        )
        for term in search_terms
    }

    # Loop through each page in the PDF
    for page in document:
        text = page.get_text("text")  # Extract the text from the page
        if text:
            text = text.lower()  # Convert the page text to lowercase
            for term in search_terms:
                # Count whole-word occurrences (case-insensitive)
                keyword_counts[term] += len(patterns[term].findall(text))

    document.close()
    return keyword_counts


def analyze_folder(folder_path, search_terms, output_csv):
    # Prepare the CSV file to store the results
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row: filename + search terms
        header = ['filename'] + search_terms
        writer.writerow(header)

        # Loop through all PDF files in the folder
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                # Count the keywords in the PDF
                keyword_counts = count_keywords_in_pdf(pdf_path, search_terms)
                # Write the results for the current PDF file to the CSV
                row = [filename] + [keyword_counts[term] for term in search_terms]
                writer.writerow(row)


# Example usage
folder_path = "D:/OneDrive - The Francis Crick Institute/Sandwich Students/2027/CVs"  # Folder containing PDF files
search_terms = ['cell', 'FIJI', 'CellProfiler', 'microscop', 'python', 'matlab', 'code', 'coding', 'script', 'data',
                'analysis', 'comput', 'model', 'fluoresc', 'slide', 'rstudio', 'graphpad', 'prism', 'statistic',
                'program', 'machine', 'learning', 'imag']
output_csv = "keyword_counts.csv"

analyze_folder(folder_path, search_terms, output_csv)
