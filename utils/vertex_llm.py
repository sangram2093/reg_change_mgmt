import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()

def init_vertexai():
    token_path = os.path.join(os.getenv("WIF_HOME"), "wif_token.txt")
    with open(token_path, "r") as f:
        access_token = f.read().strip()

    credentials = Credentials(
        token=access_token,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    vertexai.init(
        project=os.getenv("PROJECT_NAME"),
        location=os.getenv("LOCATION"),
        credentials=credentials
    )

def get_summary_entities(text):
    model = GenerativeModel(os.getenv("GEMINI_MODEL"))
    prompt = (
        "Extract subjects (actors), verbs, and objects (entities) from the following regulation text. "
        "Provide a JSON with unique IDs. Show relations clearly.\n\n"
        f"{text}"
    )
    response = model.generate_content(prompt)
    return response.text
