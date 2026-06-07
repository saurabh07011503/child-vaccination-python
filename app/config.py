import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load env variables from the server/.env file and server_py/.env file
env_path_server = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server/.env'))
load_dotenv(dotenv_path=env_path_server)

env_path_py = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv(dotenv_path=env_path_py)

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    PORT: int = int(os.getenv("PORT", 5000))
    ENV: str = os.getenv("NODE_ENV", "development")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASS: str = os.getenv("EMAIL_PASS", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecurejwtsecretkey987654321")
    JWT_EXPIRE: str = os.getenv("JWT_EXPIRE", "7d")
    
    # Twilio Configuration for SMS & WhatsApp
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    
    # CallMeBot Free WhatsApp API key (personal use only — sends to your phone)
    CALLMEBOT_API_KEY: str = os.getenv("CALLMEBOT_API_KEY", "")
    
    # TextMeBot — send WhatsApp to any number (get key by email from textmebot.com)
    TEXTMEBOT_API_KEY: str = os.getenv("TEXTMEBOT_API_KEY", "")

settings = Settings()
