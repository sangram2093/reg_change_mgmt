import os
from pathlib import Path
from google.oauth2.credentials import Credentials
import vertexai
from langchain.vectorstores import FAISS
from langchain.embeddings import VertexAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.llms import VertexAI

# Load token from file
WIF_HOME = os.environ.get("WIF_HOME", ".")
WIF_TOKEN_FILENAME = os.path.join(WIF_HOME, "wif_token.txt")
with open(WIF_TOKEN_FILENAME, "r") as file:
    access_token = file.read().strip()

# Create Credentials object
credentials = Credentials(
    token=access_token,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("PROJECT_NAME", "your-project-id"),
    location=os.environ.get("LOCATION", "your-location"),
    credentials=credentials
)

def create_vectorstore_from_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load_and_split()
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = VertexAIEmbeddings()
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local("vectorstore")
    return db

def load_vectorstore():
    embeddings = VertexAIEmbeddings()
    return FAISS.load_local("vectorstore", embeddings)

def get_answer(query):
    db = load_vectorstore()
    llm = VertexAI(model_name=os.getenv("GEMINI_MODEL", "gemini-pro"), temperature=0.2, max_output_tokens=1024)
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=db.as_retriever())
    return qa_chain.run(query)
