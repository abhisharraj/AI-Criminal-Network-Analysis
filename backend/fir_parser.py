import os
from pypdf import PdfReader


class FIRParser:
    """
    Reads FIR files in TXT or PDF format
    and returns their text content.
    """

    SUPPORTED_EXTENSIONS = {".txt", ".pdf"}

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a TXT or PDF file.
        """

        extension = os.path.splitext(file_path)[1].lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Unsupported file type. Please upload a TXT or PDF file."
            )

        if extension == ".txt":
            return self._extract_from_txt(file_path)

        if extension == ".pdf":
            return self._extract_from_pdf(file_path)

        return ""

    def _extract_from_txt(self, file_path: str) -> str:
        """
        Extract text from a text file.
        """

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        return text.strip()

    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a text-based PDF.
        """

        reader = PdfReader(file_path)

        pages_text = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                pages_text.append(page_text)

        return "\n".join(pages_text).strip()