from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")  # Load environment variables from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")