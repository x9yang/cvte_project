import io
from typing import Optional
from PyPDF2 import PdfReader
from docx import Document


class ContractParser:
    """合同文件解析器"""

    @staticmethod
    def parse_pdf(file_content: bytes) -> dict:
        """解析PDF文件"""
        reader = PdfReader(io.BytesIO(file_content))
        pages = len(reader.pages)

        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        return {
            "pages": pages,
            "word_count": len(text),
            "text_content": text
        }

    @staticmethod
    def parse_docx(file_content: bytes) -> dict:
        """解析Word文件"""
        doc = Document(io.BytesIO(file_content))
        pages = 1  # Word没有明确页数，估算

        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"

        # 估算页数 (约500字/页)
        estimated_pages = max(1, len(text) // 500)

        return {
            "pages": estimated_pages,
            "word_count": len(text),
            "text_content": text
        }

    @classmethod
    def parse(cls, filename: str, file_content: bytes) -> Optional[dict]:
        """根据文件类型自动选择解析器"""
        result = None
        if filename.lower().endswith(".pdf"):
            result = cls.parse_pdf(file_content)
        elif filename.lower().endswith((".docx", ".doc")):
            result = cls.parse_docx(file_content)

        if result:
            print(f"[解析结果] 文件: {filename}, 页数: {result['pages']}, 字数: {result['word_count']}, 内容预览: {result['text_content'][:]}...")

        return result
