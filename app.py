import os
from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase
from google.oauth2.credentials import Credentials
import vertexai
from vertexai.generative_models import GenerativeModel
import fitz  # PyMuPDF
import uuid
import json

app = Flask(__name__)
CORS(app)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Vertex AI setup
WIF_HOME = os.environ.get("WIF_HOME")
WIF_TOKEN_FILENAME = os.path.join(WIF_HOME, "wif_token.txt")
PROJECT_NAME = os.environ.get("PROJECT_NAME")
LOCATION = os.environ.get("LOCATION")
MODEL_NAME = os.environ.get("GEMINI_MODEL")

with open(WIF_TOKEN_FILENAME, "r") as file:
    access_token = file.read().strip()

credentials = Credentials(
    token=access_token,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
vertexai.init(project=PROJECT_NAME, location=LOCATION, credentials=credentials)
model = GenerativeModel(MODEL_NAME)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def generate_graph_from_text(text, version):
    prompt = f"""
You are an AI assistant analyzing financial regulations.

Read the following regulation and extract entities, actions, and relationships.

1. Identify all unique subjects (entities initiating action).
2. Identify all unique objects (entities receiving action).
3. Extract verbs (actions) linking subjects and objects.
4. Assign unique IDs (like E1, E2...) to each subject and object.
5. Return as a list of nodes and edges with properties:
- node: id, name, type, version
- edge: subject_id, subject_name, object_id, object_name, name (action), confidence_score, version

Regulation:
{text}
"""
    response = model.generate_content(prompt)
    return response.text

def parse_and_store_graph(response_text, version):
    try:
        data = json.loads(response_text)
    except Exception as e:
        print("Error parsing response from Gemini:", e)
        return

    entities = data.get("entities", [])
    relationships = data.get("relationships", [])

    with driver.session() as session:
        session.run("MATCH (n:Entity {version: $version}) DETACH DELETE n", version=version)

        for ent in entities:
            session.run(
                "CREATE (e:Entity {id: $id, name: $name, type: $type, version: $version})",
                id=ent["id"], name=ent["name"], type=ent.get("type", "Unknown"), version=version
            )

        for rel in relationships:
            session.run(
                """
                MATCH (a:Entity {id: $subject_id, version: $version})
                MATCH (b:Entity {id: $object_id, version: $version})
                CREATE (a)-[:ACTION {
                    name: $name,
                    subject_name: $subject_name,
                    object_name: $object_name,
                    confidence_score: $confidence_score,
                    version: $version
                }]->(b)
                """,
                subject_id=rel["subject_id"],
                object_id=rel["object_id"],
                name=rel["name"],
                subject_name=rel["subject_name"],
                object_name=rel["object_name"],
                confidence_score=rel.get("confidence_score", 1.0),
                version=version
            )

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        old_path = request.form.get("old_path")
        new_path = request.form.get("new_path")

        old_text = extract_text_from_pdf(old_path)
        new_text = extract_text_from_pdf(new_path)

        old_graph = generate_graph_from_text(old_text, "old")
        new_graph = generate_graph_from_text(new_text, "new")

        parse_and_store_graph(old_graph, "old")
        parse_and_store_graph(new_graph, "new")

        return redirect(url_for("compare"))

    return render_template("index.html")

@app.route("/compare")
def compare():
    return render_template("compare.html")

@app.route("/graph_data/<version>")
def get_graph_data(version):
    if version not in ["old", "new"]:
        return jsonify({"error": "Invalid version"}), 400

    with driver.session() as session:
        result = session.run(
            "MATCH (a:Entity {version: $version})-[r:ACTION]->(b:Entity {version: $version}) RETURN a, r, b",
            version=version
        )

        nodes = {}
        edges = []

        for record in result:
            a = record["a"]
            b = record["b"]
            r = record["r"]

            a_id = a["id"]
            b_id = b["id"]
            a_name = a.get("name", a_id)
            b_name = b.get("name", b_id)

            nodes[a_id] = {"id": a_id, "label": a_name, "group": a.get("type", "Entity")}
            nodes[b_id] = {"id": b_id, "label": b_name, "group": b.get("type", "Entity")}

            edge_label = f"{r['name']} ({round(r.get('confidence_score', 1.0), 2)})"
            edges.append({"from": a_id, "to": b_id, "label": edge_label})

        return jsonify({"nodes": list(nodes.values()), "edges": edges})
