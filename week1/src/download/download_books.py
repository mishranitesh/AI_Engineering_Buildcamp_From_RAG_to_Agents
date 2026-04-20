import os
import csv
import requests


def download_books(csv_path: str, output_dir: str):
    """
    Download all PDF books listed in a CSV file.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file containing book metadata.

    output_dir : str
        Directory where downloaded PDF files will be stored.

    Expected CSV columns
    --------------------
    - title   : name of the book
    - pdf_url : direct link to the PDF file
    """

    # Create the output directory if it does not already exist
    os.makedirs(output_dir, exist_ok=True)

    # Open the CSV file and read each row as a dictionary
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Loop through each row in the CSV
        for row in reader:
            # Read the book title from the CSV
            title = row["title"]

            # Read the direct PDF download URL from the CSV
            pdf_url = row["pdf_url"]

            # Build a filesystem-safe PDF filename from the title
            # Example: "Think Python 2e" -> "think_python_2e.pdf"
            filename = title.lower().replace(" ", "_").replace("/", "_") + ".pdf"

            # Create the full path where the PDF will be saved
            filepath = os.path.join(output_dir, filename)

            # Skip download if the file is already present
            if os.path.exists(filepath):
                print(f"Skipping existing file: {filename}")
                continue

            print(f"Downloading: {title}")

            try:
                # Send HTTP request to the PDF URL
                response = requests.get(pdf_url, timeout=30)

                # Raise an exception if the request failed
                response.raise_for_status()

                # Write the PDF content in binary mode
                with open(filepath, "wb") as out:
                    out.write(response.content)

                print(f"Saved to: {filepath}")

            except Exception as e:
                # Print the error and continue with the next file
                print(f"Failed to download {title}: {e}")