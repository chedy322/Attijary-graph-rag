from unstructured.partition.auto import partition
from flask import current_app
import os


def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file using PyPDF2.

    Args:
        file_path (str): The path to the PDF file.
    Returns:
        A list of dictionaries containing the extracted text, page number,  category and filename for each page.
    """
    current_app.logger.info(f"Extracting text from PDF: {file_path}")
    # IS_PROD=True if os.getenv("FLASK_ENV") == "production" else False
    elements = partition(filename=file_path)

    # Categories you generally want to IGNORE for GraphRAG
    ignored_categories = {"Header", "Footer", "PageNumber"}

    extracted_records = []

    for element in elements:
        # 1. Access page number safely (defaults to 1 if not detected)
        page_num = getattr(element.metadata, "page_number", 1)

        # 2. Skip structural noise like running headers/footers
        if element.category in ignored_categories:
            continue

        text = element.text.strip()

        # 3. Filter short/junk text
        if len(text) < 3:
            continue

        extracted_records.append(
            {
                "page_number": page_num,
                "text": text,
                "file_name": os.path.basename(file_path),
            }
        )

    current_app.logger.info(
        f"Extracted {len(extracted_records)} text records from PDF: {file_path}"
    )
    return extracted_records


# print(extract_text_from_pdf("../files/motivation_letter.pdf"))  # Example usage for testing
