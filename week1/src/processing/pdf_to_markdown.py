import os
from markitdown import MarkItDown


def convert_pdf_to_markdown(input_path: str, output_path: str):
    """
    Convert one PDF file to a Markdown file.

    Parameters
    ----------
    input_path : str
        Path to the source PDF file.

    output_path : str
        Path where the converted Markdown file should be written.
    """

    # Create one MarkItDown converter instance
    md = MarkItDown()

    # Convert the PDF into a MarkItDown result object
    result = md.convert(input_path)

    # In current markitdown versions, the extracted markdown/text
    # is available on the `text_content` attribute
    markdown_text = result.text_content

    # Write the converted markdown to disk
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)


def convert_all(input_dir: str, output_dir: str):
    """
    Convert all PDFs in a folder into Markdown files.

    Parameters
    ----------
    input_dir : str
        Folder containing PDF files.

    output_dir : str
        Folder where Markdown files will be saved.
    """

    # Ensure output folder exists
    os.makedirs(output_dir, exist_ok=True)

    # Loop through all files in the input folder
    for filename in os.listdir(input_dir):
        # Only process PDF files
        if not filename.endswith(".pdf"):
            continue

        input_path = os.path.join(input_dir, filename)
        output_filename = filename.replace(".pdf", ".md")
        output_path = os.path.join(output_dir, output_filename)

        # Skip files already converted
        if os.path.exists(output_path):
            print(f"Skipping existing file: {output_filename}")
            continue

        print(f"Converting: {filename}")

        try:
            convert_pdf_to_markdown(input_path, output_path)
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f"Failed to convert {filename}: {e}")