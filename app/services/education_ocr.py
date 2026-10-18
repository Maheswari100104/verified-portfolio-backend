from io import BytesIO

import pytesseract
from PIL import Image


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# =========================================================
# Extract Text From Image
# =========================================================

def extract_text_from_image(
    file_data: bytes,
) -> str:
    """
    Extract text from an image using Tesseract OCR.
    """

    try:
        image = Image.open(
            BytesIO(file_data)
        )

        text = pytesseract.image_to_string(
            image
        )

        return text.strip()

    except Exception as error:
        raise RuntimeError(
            f"Unable to extract text from image: {error}"
        )