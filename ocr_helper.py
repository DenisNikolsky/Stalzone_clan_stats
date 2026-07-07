import pytesseract
from PIL import Image
import os
import sys

def resource_path(relative_path):
    """Возвращает абсолютный путь к файлу, работающий в .exe и в .py"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Указываем путь к tesseract.exe внутри папки Tesseract-OCR
tesseract_path = resource_path(os.path.join("Tesseract-OCR", "tesseract.exe"))
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Указываем путь к tessdata (папка с языковыми файлами)
tessdata_dir = resource_path(os.path.join("Tesseract-OCR", "tessdata"))
os.environ['TESSDATA_PREFIX'] = tessdata_dir

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='rus+eng')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines
    except Exception as e:
        raise RuntimeError(f"Ошибка при распознавании: {e}")