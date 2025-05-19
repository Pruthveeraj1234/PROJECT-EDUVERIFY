import os
import uuid
import logging
import mimetypes
import cv2
import pytesseract
import numpy as np
from PIL import Image
from difflib import SequenceMatcher
from pdf2image import convert_from_path
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from deepface import DeepFace
from decouple import config

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SIMILARITY_THRESHOLD = float(config("SIMILARITY_THRESHOLD", default=0.85))
FACE_THRESHOLD = float(config("FACE_THRESHOLD", default=0.5))
BLUR_THRESHOLD = int(config("BLUR_THRESHOLD", default=100))


# ====================== Helper Functions ======================

def is_blurry(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return True
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
    return fm < BLUR_THRESHOLD


def convert_to_image(file_path, mime_type):
    if mime_type.startswith("image"):
        return file_path
    elif mime_type == "application/pdf":
        images = convert_from_path(file_path)
        if not images:
            raise ValueError("PDF has no pages")
        image_path = f"{file_path}_page1.jpg"
        images[0].save(image_path, "JPEG")
        return image_path
    else:
        raise ValueError("Unsupported file type")


def extract_text(image_path):
    if is_blurry(image_path):
        raise ValueError("Image is too blurry to process. Please upload a clearer version.")
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)


def extract_field(text, field_type):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        if field_type.lower() in line.lower():
            return line.split(":")[-1].strip()
    return lines[0] if lines else None


def contains_pass_status(text):
    return "pass" in text.lower()


def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()


def verify_selfie(selfie_path, gov_id_photo_path):
    try:
        result = DeepFace.verify(img1_path=selfie_path, img2_path=gov_id_photo_path, enforce_detection=False)
        return result["verified"], result["distance"]
    except Exception as e:
        logger.exception("Face verification failed")
        return False, 1.0


def send_to_bubble(data):
    try:
        import requests
        bubble_url = config("BUBBLE_API_URL")
        headers = {"Content-Type": "application/json"}
        response = requests.post(bubble_url, json=data, headers=headers)
        return response.status_code == 200
    except Exception as e:
        logger.exception("Failed to send data to Bubble.io")
        return False


# ====================== Main Verification View ======================

@csrf_exempt
@require_POST
def verify(request):
    try:
        form = request.POST
        files = request.FILES

        # Basic field extraction
        user_type = form.get("user_type")
        name = form.get("name")
        email = form.get("email")
        contact = form.get("contact")
        college_name = form.get("college_name", "")
        college_id = form.get("college_id", "")
        government_id = form.get("government_id")

        required_fields = [user_type, name, email, contact, government_id]
        if not all(required_fields):
            return HttpResponse("Missing required form fields", status=400)

        if user_type == "student" and (not college_name or not college_id):
            return HttpResponse("College name and ID are required for students", status=400)
        if user_type == "employee" and "graduate_certificate" not in files:
            return HttpResponse("Graduate certificate required for employees", status=400)

        # Uploaded files
        file_fields = {
            "college_id_photo": files.get("college_id_photo"),
            "gov_id_photo": files.get("gov_id_photo"),
            "selfie": files.get("selfie"),
            "ssc_certificate": files.get("ssc_certificate"),
            "graduate_certificate": files.get("graduate_certificate") if user_type == "employee" else None,
        }

        for key, file in file_fields.items():
            if key != "graduate_certificate" and not file:
                return HttpResponse(f"{key.replace('_', ' ').capitalize()} is required", status=400)

        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        fs = FileSystemStorage(location=upload_dir)
        file_paths = {}

        for field, file in file_fields.items():
            if file:
                unique_filename = f"{uuid.uuid4().hex}{os.path.splitext(file.name)[1]}"
                filename = fs.save(unique_filename, file)
                file_path = fs.path(filename)
                mime_type, _ = mimetypes.guess_type(file_path)
                file_paths[field] = convert_to_image(file_path, mime_type or "")

        # Extract text from documents
        try:
            college_text = extract_text(file_paths["college_id_photo"])
            gov_text = extract_text(file_paths["gov_id_photo"])
            ssc_text = extract_text(file_paths["ssc_certificate"])
            grad_text = extract_text(file_paths["graduate_certificate"]) if user_type == "employee" else ""
        except ValueError as ve:
            return HttpResponse(str(ve), status=400)
        except Exception as e:
            return HttpResponse(f"Error reading documents: {str(e)}", status=400)

        if not contains_pass_status(ssc_text):
            return HttpResponse("SSC certificate does not indicate PASS status", status=400)

        # Field extraction
        extracted = {
            "college_id_name": extract_field(college_text, "Name"),
            "college_id_num": extract_field(college_text, "ID"),
            "gov_name": extract_field(gov_text, "Name"),
            "gov_id": extract_field(gov_text, "ID"),
            "gov_dob": extract_field(gov_text, "DOB"),
            "ssc_name": extract_field(ssc_text, "Name"),
            "ssc_dob": extract_field(ssc_text, "DOB"),
            "grad_name": extract_field(grad_text, "Name") if grad_text else None,
        }

        # Check name similarity
        for doc_name, value in [
            ("College ID", extracted["college_id_name"]),
            ("Government ID", extracted["gov_name"]),
            ("SSC", extracted["ssc_name"])
        ]:
            if not value or ratio(name.lower(), value.lower()) < SIMILARITY_THRESHOLD:
                return HttpResponse(f"Name mismatch in {doc_name}: found '{value}'", status=400)

        if user_type == "employee" and extracted["grad_name"]:
            if ratio(name.lower(), extracted["grad_name"].lower()) < SIMILARITY_THRESHOLD:
                return HttpResponse(f"Name mismatch in graduate certificate: '{extracted['grad_name']}'", status=400)

        # ID matching
        if college_id and extracted["college_id_num"] and college_id.lower() != extracted["college_id_num"].lower():
            return HttpResponse("College ID mismatch", status=400)
        if government_id and extracted["gov_id"] and government_id.lower() != extracted["gov_id"].lower():
            return HttpResponse("Government ID mismatch", status=400)

        # ✅ Check selfie blur before face verification
        if is_blurry(file_paths["selfie"]):
            return HttpResponse("Selfie is too blurry to process. Please re-upload a clearer photo.", status=400)

        selfie_path = file_paths["selfie"]
        gov_photo_path = file_paths["gov_id_photo"]
        face_match, face_distance = verify_selfie(selfie_path, gov_photo_path)

        if not face_match or face_distance > FACE_THRESHOLD:
            return HttpResponse("Selfie and Government ID photo do not match", status=400)

        # Send data to Bubble.io
        bubble_data = {
            "name": name,
            "email": email,
            "contact": contact,
            "college_name": college_name,
            "college_id": college_id,
            "government_id": government_id,
            "verification_status": "verified",
            "user_type": user_type,
        }

        if not send_to_bubble(bubble_data):
            return HttpResponse("Failed to send verification result to Bubble.io", status=500)

        return HttpResponse("Verification successful", status=200)

    except Exception as e:
        logger.exception("Unexpected error in verification:")
        return HttpResponse(f"Verification failed: {str(e)}", status=500)
