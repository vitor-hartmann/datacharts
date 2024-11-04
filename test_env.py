import os
from dotenv import load_dotenv

# Get absolute path to .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

print(f"Looking for .env file at: {ENV_PATH}")
print(f".env file exists: {os.path.exists(ENV_PATH)}")

# Load the .env file
load_dotenv(ENV_PATH)

# Get and check the API key
api_key = os.getenv('ANTHROPIC_API_KEY')

if api_key:
    print(f"API key found!")
    print(f"Key starts with: {api_key[:10]}")
    print(f"Key length: {len(api_key)}")
    print(f"Key format correct: {api_key.startswith('sk-ant')}")
else:
    print("No API key found!") 