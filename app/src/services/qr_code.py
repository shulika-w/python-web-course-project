"""
module to work with QR-code
"""
from io import BytesIO
import qrcode
def generate_qr_code(image_url: str) -> BytesIO:
    """
    Generates a PNG image with a QR code from the url of the image:
    :param uuid: UUID of the image
    :type uuid: str.
    :return FileResponse: File in image/png format with QR-code url.
    :rtype BytesIO:
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
    )
    # Add URL to QR-code
    qr.add_data(image_url)
    qr.make(fit=True)
    # Make QR-code object
    qr_code = qr.make_image(fill_color="black", back_color="white")
    # Save QR-code to byte object
    qr_code_bytes = BytesIO()
    qr_code.save(qr_code_bytes)
    qr_code_bytes.seek(0)
    return qr_code_bytes