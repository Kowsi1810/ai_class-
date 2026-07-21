# ==========================================
# parser.py
# Resume Parsing Module
# ==========================================

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ResumeParser:
    """
    ResumeParser is responsible for

    1. Reading PDF files
    2. Extracting text
    3. Cleaning text
    4. Splitting text into chunks
    """

    def __init__(self, chunk_size=500, chunk_overlap=100):
        """
        Initialize the parser.

        Parameters
        ----------
        chunk_size:
            Maximum number of characters in one chunk.

        chunk_overlap:
            Number of overlapping characters between chunks.
        """

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def extract_text(self, pdf_path):
        """
        Extract all text from a PDF.

        Parameters
        ----------
        pdf_path : str

        Returns
        -------
        str
        """

        text = ""

        document = fitz.open(pdf_path)

        for page in document:
            text += page.get_text()

        document.close()

        return text

    def clean_text(self, text):
        """
        Clean extracted text.
        """

        text = text.replace("\n", " ")

        text = " ".join(text.split())

        return text

    def split_text(self, text):
        """
        Split resume into chunks.
        """

        chunks = self.text_splitter.split_text(text)

        return chunks

    def parse_resume(self, pdf_path):
        """
        Complete resume pipeline.
        """

        text = self.extract_text(pdf_path)

        cleaned_text = self.clean_text(text)

        chunks = self.split_text(cleaned_text)

        return chunks