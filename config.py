"""
Configuration settings for the Career Up application
"""

import os

# Directory paths
BASE_DIR = "D:/programs/Docker_strange/cursor/intelligent_career_advisior"
# Update OUTPUT_DIR to be in the current workspace
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
INPUT_DIR = os.path.join(BASE_DIR, 'input')

# File paths
RESUME_PDF = os.path.join(INPUT_DIR, 'resume.pdf')
STRUCTURED_RESUME_JSON = os.path.join(OUTPUT_DIR, 'structured_resume.json')
JOB_MATCHES_JSON = os.path.join(OUTPUT_DIR, 'job_matches.json')
CAREER_GUIDANCE_JSON = os.path.join(OUTPUT_DIR, 'career_guidance.json')
INTERVIEW_PREP_JSON = os.path.join(OUTPUT_DIR, 'interview_prep.json')
CONVERSATION_JSON = os.path.join(OUTPUT_DIR, 'conversation.json')

# API Keys
# GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', 'AIzaSyBhKw15YzK6ab9Sh_lf2FBGHPY3PwDKiHA')
GOOGLE_API_KEY = "AIzaSyBhKw15YzK6ab9Sh_lf2FBGHPY3PwDKiHA"
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'your-api-key-here')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Other configuration settings
MAX_JOBS_TO_RETURN = 10

# File paths for resume samples
RESUME_SAMPLES_DIR = os.path.join(BASE_DIR, "resume_samples")

# Create directories if they don't exist
os.makedirs(RESUME_SAMPLES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Path for Sample_resume.pdf
SAMPLE_RESUME_PATH = os.path.join(RESUME_SAMPLES_DIR, "Sample_resume.pdf")

# Model configurations
RESUME_PARSER_MODEL = "gemini-1.5-pro"
JOB_MATCHER_MODEL = "gemini-1.5-pro"

# File Paths
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')

# Email Configuration
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'your-email@example.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your-email-password')

# Database Configuration (override in run.py or local environment)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
DB_DATABASE = os.environ.get('DB_DATABASE', 'career_up')

# Misc Settings
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-for-sessions')
