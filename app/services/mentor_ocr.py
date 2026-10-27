
from io import BytesIO
import os
import shutil

import pytesseract
from PIL import Image


# =========================================================
# Tesseract OCR Configuration
# =========================================================

def configure_tesseract() -> None:
    """
    Configure Tesseract OCR for Windows and Linux.
    Tesseract must be installed and available in PATH.
    """

    tesseract_path = shutil.which("tesseract")

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    elif os.name == "nt":
        windows_tesseract = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

        if os.path.isfile(windows_tesseract):
            pytesseract.pytesseract.tesseract_cmd = (
                windows_tesseract
            )
        else:
            raise RuntimeError(
                "Tesseract OCR is not installed or is not "
                "available in PATH. Install Tesseract OCR "
                "and configure its executable path."
            )

    else:
        raise RuntimeError(
            "Tesseract OCR was not found. Install it in the "
            "server environment and make sure the tesseract "
            "executable is available in PATH."
        )


configure_tesseract()


# =========================================================
# Extract Text From Image
# =========================================================

def extract_text_from_image(
    file_data: bytes,
) -> str:
    """
    Extract text from an image using Tesseract OCR.

    Args:
        file_data: Image contents as bytes.

    Returns:
        Extracted text as a string.

    Raises:
        RuntimeError: If image processing or OCR fails.
    """

    try:
        if not file_data:
            raise ValueError("The uploaded image is empty.")

        image = Image.open(BytesIO(file_data))
        image.load()

        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        text = pytesseract.image_to_string(image)

        return text.strip()

    except Exception as error:
        raise RuntimeError(
            f"Unable to extract text from image: {error}"
        ) from error
