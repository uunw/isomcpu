"""
Configuration settings for the application.
"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_DATABASE_URL")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "insecure-dev-secret-key-change-me")

# Deployment URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://isomcpu.duckdns.org")
