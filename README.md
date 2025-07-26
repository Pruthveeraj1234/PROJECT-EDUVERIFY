
# EduVerify

EduVerify is a Django-based application that verifies user identities by processing college IDs, government IDs, selfies, and certificates. It uses OCR, face recognition, and integrates with Bubble.io for frontend and data storage.
-  Document verification using **DigiLocker API**
-  Secure credential handling with environment-based secrets
-  Integrated logging and error tracking
-  Optional integration with **Bubble.io** for frontend workflows
-  Lightweight SQLite backend for local development
-  Modular Django project structure.


---

## 🛠️ Tech Stack

- **Backend**: Django (Python 3.10)
- **Database**: SQLite (dev) | PostgreSQL (prod-ready)
- **API Integration**: [DigiLocker Developer APIs](https://developer.digilocker.gov.in/)
- **Frontend (optional)**: Bubble.io or Django Templates
- **Auth**: Basic session-based or OAuth (if extended)

---


## Setup Instructions

1. **Clone the Repository** (if applicable):

## 🔧 Installation

###  1. Clone & Setup Virtual Environment

```bash
git clone https://github.com/Pruthveeraj1234/PROJECT-EDUVERIFY.git
cd PROJECT-EDUVERIFY
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

##install requirments.
pip install -r requirements.txt

## Configure.env
SECRET_KEY=your-django-secret-key
DEBUG=True
DIGILOCKER_CLIENT_ID=your-client-id
DIGILOCKER_CLIENT_SECRET=your-client-secret

## Run & Migrations and Run server
python manage.py migrate
python manage.py runserver




