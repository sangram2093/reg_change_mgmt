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
    prompt = f"""
    You are an AI assistant for analyzing financial regulation documents. From the following regulation text, perform the following:
    
    1. Extract all relevant **entities** (e.g., organizations, individuals, processes, obligations, legal terms).
    2. Assign each entity a **globally unique ID**. These IDs will be used for connecting relationships.
    3. Identify **all relationships** as (subject, verb, object) triples. Use only the extracted entities as subject and object.
    4. Return the result in valid compact JSON with two keys: `entities` and `relationships`.
    
    Rules:
    - Use only extracted entities (not raw text) in relationships.
    - `entities` should have `id`, `name`, and optional `type` (e.g., organization, obligation, action).
    - `relationships` should have `subject_id`, `verb`, and `object_id`.
    - Do NOT include explanations, markdown, or comments.
    
    Input Regulation Text:
    {text}
    """

    response = model.generate_content(prompt)
    return response.text
