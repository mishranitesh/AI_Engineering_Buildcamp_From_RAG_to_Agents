"""
Entry-point script to download all books.

This script simply calls the reusable download function
from the src layer. This separation keeps business logic
clean and reusable.
"""

from src.download.download_books import download_books


# Call the function with:
# - path to CSV file (input)
# - output directory where PDFs will be saved
download_books(
    csv_path="data/raw/books.csv",
    output_dir="data/raw/pdfs/"
)