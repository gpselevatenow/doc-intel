import os
from docling.document_converter import DocumentConverter

def parse_document(file_path: str):
    """
    Wrapper around Docling to parse uploaded PDFs into Markdown,
    preserving table structures.
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    markdown_text = result.document.export_to_markdown()
    docling_doc = result.document
    return markdown_text, docling_doc
