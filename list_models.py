import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# Get the directory containing this script
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please set it in your .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Get available models
try:
    models = client.models.list()
    
    print("\nAvailable OpenAI Models:")
    print("=======================")
    
    for model in models.data:
        print(f"- {model.id}")
    
except Exception as e:
    print(f"Error listing models: {str(e)}") 