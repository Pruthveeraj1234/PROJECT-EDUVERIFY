import os
import logging
import mimetypes
import requests
import uuid
import re
import cv2
import numpy as np
import pytesseract
import tensorflow as tf

from PIL import Image
from pdf2image import convert_from_path
from Levenshtein import ratio
from deepface import DeepFace
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from decouple import config

# Optional: set tesseract path if not in system path
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Logging
logger = logging.getLogger(__name__)

# Thresholds (from settings or .env)
SIMILARITY_THRESHOLD = float(config("SIMILARITY_THRESHOLD", default=0.85))
FACE_THRESHOLD = float(config("FACE_THRESHOLD", default=0.5))
BLUR_THRESHOLD = int(config("BLUR_THRESHOLD", default=100))

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Unable to load image")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

def is_blurry(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return True
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
    return fm < BLUR_THRESHOLD

def extract_text(image_path):
    if is_blurry(image_path):
        raise ValueError(f"{os.path.basename(image_path)} is too blurry to read. Please re-upload.")
    pil_img = Image.fromarray(preprocess_image(image_path))
    text = pytesseract.image_to_string(pil_img, config="--oem 3 --psm 6", lang="eng")
    return text.strip()

def convert_to_image(file_path, mime_type):
    if "pdf" in mime_type.lower():
        images = convert_from_path(file_path)
        if not images:
            raise ValueError("Failed to convert PDF to image")
        output_path = file_path.rsplit(".", 1)[0] + ".jpg"
        images[0].save(output_path, "JPEG")
        return output_path
    return file_path

def extract_field(text, field_name):
    match = re.search(rf"{field_name}\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def contains_pass_status(text):
    return "pass" in text.lower() or "passed" in text.lower()

def verify_selfie(selfie_path, id_photo_path):
    try:
        result = DeepFace.verify(img1_path=selfie_path, img2_path=id_photo_path, distance_metric="cosine")
        return result["verified"], result["distance"]
    except Exception as e:
        logger.error(f"Face match error: {str(e)}")
        return False, 1.0

def send_to_bubble(data):
    bubble_url = config("BUBBLE_API_URL")
    bubble_api_key = config("BUBBLE_API_KEY")
    headers = {
        "Authorization": f"Bearer {bubble_api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = "&".join([f"{key}={value}" for key, value in data.items()])
    try:
        response = requests.post(bubble_url, headers=headers, data=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error sending to Bubble.io: {str(e)}")
        return False

@csrf_exempt
@require_POST
def verify(request):
    try:
        form = request.POST
        files = request.FILES

        user_type = form.get("user_type")
        name = form.get("name")
        email = form.get("email")
        contact = form.get("contact")
        college_name = form.get("college_name", "")
        college_id = form.get("college_id", "")
        government_id = form.get("government_id")

        required_fields = [user_type, name, email, contact, government_id]
        if not all(required_fields):
            return HttpResponse("Missing basic form fields", status=400)

        if user_type == "student" and (not college_name or not college_id):
            return HttpResponse("College name and ID are required for students", status=400)
        if user_type == "employee" and "graduate_certificate" not in files:
            return HttpResponse("Graduate certificate required for employees", status=400)

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

        try:
            college_text = extract_text(file_paths["college_id_photo"])
            gov_text = extract_text(file_paths["gov_id_photo"])
            ssc_text = extract_text(file_paths["ssc_certificate"])
            grad_text = extract_text(file_paths["graduate_certificate"]) if user_type == "employee" else ""
        except Exception as e:
            return HttpResponse(str(e), status=400)

        if not contains_pass_status(ssc_text):
            return HttpResponse("SSC certificate does not indicate PASS status", status=400)

        # Extracted fields
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

        for doc_name, value in [
            ("College ID", extracted["college_id_name"]),
            ("Gov ID", extracted["gov_name"]),
            ("SSC", extracted["ssc_name"])
        ]:
            if not value or ratio(name.lower(), value.lower()) < SIMILARITY_THRESHOLD:
                return HttpResponse(f"Name mismatch in {doc_name}: found '{value}'", status=400)

        if user_type == "employee" and extracted["grad_name"]:
            if ratio(name.lower(), extracted["grad_name"].lower()) < SIMILARITY_THRESHOLD:
                return HttpResponse(f"Name mismatch in graduate certificate: '{extracted['grad_name']}'", status=400)

        if college_id and extracted["college_id_num"] and college_id.lower() != extracted["college_id_num"].lower():
            return HttpResponse("College ID mismatch", status=400)
        if government_id and extracted["gov_id"] and government_id.lower() != extracted["gov_id"].lower():
            return HttpResponse("Government ID mismatch", status=400)
        if extracted["gov_dob"] != extracted["ssc_dob"]:
            return HttpResponse("DOB mismatch between government ID and SSC", status=400)

        is_face_matched, distance = verify_selfie(file_paths["selfie"], file_paths["college_id_photo"])
        if not is_face_matched:
            return HttpResponse(f"Face mismatch (distance: {distance:.2f}). Please re-upload selfie.", status=403)

        bubble_data = {
            "user_type": user_type,
            "name": name,
            "email": email,
            "contact": contact,
            "college_name": college_name,
            "college_id": college_id,
            "government_id": government_id,
            "verification_status": "verified",
        }

        if send_to_bubble(bubble_data):
            return HttpResponse("Verification successful", status=200)
        else:
            return HttpResponse("Verification succeeded but failed to send data to Bubble.io", status=502)

    except Exception as e:
        logger.error(f"Unhandled verification error: {str(e)}")
        return HttpResponse(f"Verification failed: {str(e)}", status=500)
