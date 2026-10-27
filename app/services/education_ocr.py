import os
import shutil
from io import BytesIO

import pytesseract
from PIL import Image


# =========================================================
# Configure Tesseract OCR
# =========================================================

tesseract_path = shutil.which("tesseract")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

elif os.name == "nt":
    windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.exists(windows_path):
        pytesseract.pytesseract.tesseract_cmd = windows_path


# =========================================================
# Extract Text From Image
# =========================================================

def extract_text_from_image(file_data: bytes) -> str:
    """
    Extract text from an image using Tesseract OCR.
    """

    try:
        image = Image.open(BytesIO(file_data))

        text = pytesseract.image_to_string(image)

        return text.strip()

    except Exception as error:
        raise RuntimeError(
            f"Unable to extract text from image: {error}"
        ) from error