import qrcode
import os
from pathlib import Path
from app.models.models import Student


def generate_qr_code(student: Student, base_url: str = "http://localhost:8000") -> str:
    """Generate QR code for a student."""
    # Create QR code data - the URL that will be scanned
    qr_data = f"{base_url}/api/checkin/scan?student_id={student.student_id}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to file
    qr_dir = Path("qr_codes")
    qr_dir.mkdir(exist_ok=True)
    
    filename = f"student_{student.student_id}.png"
    filepath = qr_dir / filename
    img.save(filepath)
    
    return str(filepath)


def delete_qr_code(qr_code_path: str):
    """Delete a QR code file."""
    if qr_code_path and os.path.exists(qr_code_path):
        os.remove(qr_code_path)
