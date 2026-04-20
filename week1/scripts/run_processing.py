"""
Entry-point script for converting PDFs to Markdown.

Pipeline step:
    raw PDFs → processed markdown files
"""

from src.processing.pdf_to_markdown import convert_all


if __name__ == "__main__":
    convert_all(
        input_dir="data/raw/pdfs/",
        output_dir="data/processed/"
    )