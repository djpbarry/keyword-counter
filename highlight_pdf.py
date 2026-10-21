import csv
import os

import fitz  # PyMuPDF


def count_keywords_in_pdf(pdf_path, search_terms):
    document = fitz.open(pdf_path)
    keyword_counts = {term: 0 for term in search_terms}

    # Loop through each page in the PDF
    for page in document:
        text = page.get_text("text")  # Extract the text from the page
        if text:
            text = text.lower()  # Convert the page text to lowercase
            for term in search_terms:
                keyword_counts[term] += text.count(term.lower())  # Count occurrences (case-insensitive)

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
folder_path = "D:/OneDrive - The Francis Crick Institute/Sandwich Students/2025/CVs"  # Folder containing PDF files
search_terms = ['cell', 'FIJI', 'CellProfiler', 'microscop', 'python', 'matlab', 'code', 'coding', 'script', 'data',
                'analysis', 'comput', 'model', 'fluoresc', 'slide', 'rstudio', 'graphpad', 'prism', 'statistic',
                'program', 'machine', 'learning', 'imag']
output_csv = "keyword_counts.csv"

analyze_folder(folder_path, search_terms, output_csv)
