from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict
from flask import current_app
import uuid
import re
from collections import defaultdict

from matplotlib import lines


def chunk_text(pages_array: List[Dict], max_tokens=600, overlap_tokens=100):
    """
    Chunks the text from the provided pages array into smaller pieces.

    Args:
        pages_array (List[Dict]): A list of dictionaries containing the text and metadata for each page.
        max_tokens (int): The maximum number of tokens per chunk.
        overlap_tokens (int): The number of tokens to overlap between chunks.

    Returns:
        List[Dict]: A list of dictionaries containing the chunked text and metadata.
    """

    grouped_pages = defaultdict(list)
    for record in pages_array:
        key = (record.get("file_name", "doc"), record.get("page_number", 1))
        text_line = record.get("text", "").strip()
        if text_line:
            grouped_pages[key].append(text_line)

    current_app.logger.info(
        f"Chunking text with max_tokens={max_tokens} and overlap_tokens={overlap_tokens}"
    )
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4o",
        chunk_size=max_tokens,
        chunk_overlap=overlap_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    result = []
    for (file_name, page_num), lines in grouped_pages.items():
        full_page_text = " ".join(lines)
        full_page_text = re.sub(r"-\s+", "-", full_page_text)
        full_page_text = re.sub(r"\s+", " ", full_page_text).strip()
        chunks = text_splitter.split_text(full_page_text)

        for i, chunk_content in enumerate(chunks):
            unique_string = f"{file_name}_p{page_num}_c{i}"
            unique_chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))

            result.append(
                {
                    "chunk_id": unique_chunk_id,
                    "text": chunk_content,
                    "page_number": page_num,
                    "file_name": file_name,
                    "chunk_index": i,
                }
            )
    current_app.logger.info(
        f"Chunking complete. Generated {len(result)} chunks from {len(pages_array)} pages."
    )
    return result


# print(chunk_text([{"text": "This is a sample text that needs to be chunked. It contains multiple sentences and should be split into smaller pieces based on the specified maximum token limit.", "page_number": 1, "file_name": "sample.pdf"}], max_tokens=20, overlap_tokens=5))  # Example usage for testing
