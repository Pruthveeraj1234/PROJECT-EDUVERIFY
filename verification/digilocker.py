import os
import requests
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

# Load from environment or Django settings
DIGILOCKER_BASE_URL = "https://api.digitallocker.gov.in/public"
DIGILOCKER_AUTH_URL = "https://api.digitallocker.gov.in/oauth2/1/token"
CLIENT_ID = os.getenv("DIGILOCKER_CLIENT_ID", getattr(settings, "DIGILOCKER_CLIENT_ID", ""))
CLIENT_SECRET = os.getenv("DIGILOCKER_CLIENT_SECRET", getattr(settings, "DIGILOCKER_CLIENT_SECRET", ""))
REDIRECT_URI = os.getenv("DIGILOCKER_REDIRECT_URI", getattr(settings, "DIGILOCKER_REDIRECT_URI", ""))

# Step 1: Exchange authorization code for access token
def get_access_token(auth_code):
    payload = {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    try:
        response = requests.post(DIGILOCKER_AUTH_URL, data=payload)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.RequestException as e:
        print(f"[DigiLocker] Token exchange failed: {e}")
        return None

# Step 2: Fetch metadata of all issued documents
def get_issued_documents(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url = f"{DIGILOCKER_BASE_URL}/documents/issued"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()  # List of issued docs
    except requests.RequestException as e:
        print(f"[DigiLocker] Issued document fetch failed: {e}")
        return None

# Step 3: Download specific document by URI
def download_document(access_token, uri):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url = f"{DIGILOCKER_BASE_URL}/documents/uri/{uri}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"[DigiLocker] Document download failed: {e}")
        return None
