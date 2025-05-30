import os
from google.oauth2.credentials import Credentials
import vertexai
from vertexai.generative_models import GenerativeModel

def init_vertexai():
    WIF_HOME = os.environ.get("WIF_HOME")
    token_path = os.path.join(WIF_HOME, "wif_token.txt")
    with open(token_path, "r") as f:
        access_token = f.read().strip()

    credentials = Credentials(
        token=access_token,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    vertexai.init(
        project=os.environ["PROJECT_NAME"],
        location=os.environ["LOCATION"],
        credentials=credentials
    )

def get_summary_entities(text):
    model = GenerativeModel(os.environ["GEMINI_MODEL"])
    prompt = (
        "Extract subjects (actors), verbs, and objects (entities) from the following regulation text. "
        "Provide a JSON with unique IDs. Show relations clearly.\n\n"
        f"{text}"
    )
    response = model.generate_content(prompt)
    return response.text
