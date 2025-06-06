import os
from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
import vertexai
from vertexai.generative_models import GenerativeModel
import fitz
import json
import networkx as nx

app = Flask(__name__)
CORS(app)

# Store graphs in memory
graphs = {"old": nx.DiGraph(), "new": nx.DiGraph()}

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

def generate_graph_from_text(text):
    prompt = f"""
You are an AI assistant analyzing financial regulations.

Read the following regulation and extract entities, actions, and relationships.

1. Identify all unique subjects (entities initiating action).
2. Identify all unique objects (entities receiving action).
3. Extract verbs (actions) linking subjects and objects.
4. Assign unique IDs (like E1, E2...) to each subject and object.
5. Return as a list of nodes and edges with properties:
- node: id, name, type
- edge: subject_id, subject_name, object_id, object_name, name (action), confidence_score

Regulation:
{text}
"""
    response = model.generate_content(prompt)
    return response.text

def parse_and_store_graph(response_text, version):
    try:
        data = json.loads(response_text)
    except Exception as e:
        print(f"Failed to parse LLM response: {e}")
        return

    G = nx.DiGraph()

    for entity in data.get("entities", []):
        G.add_node(entity["id"], label=entity["name"], group=entity.get("type", "Entity"))

    for rel in data.get("relationships", []):
        hover_info = f"""
Optionality: {rel.get("Optionality", "N/A")}
Condition: {rel.get("Condition for Relationship to be Active", "N/A")}
Property of Object: {rel.get("Property of Object (part of condition)", "N/A")}
Thresholds: {rel.get("Thresholds", "N/A")}
Frequency: {rel.get("frequence", "N/A")}
        """.strip()

        G.add_edge(
            rel["subject_id"],
            rel["object_id"],
            label=rel.get("verb", "relates"),
            title=hover_info  # used by Vis.js for hover
        )

    graphs[version] = G

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        old_path = request.form.get("old_path")
        new_path = request.form.get("new_path")

        old_text = extract_text_from_pdf(old_path)
        new_text = extract_text_from_pdf(new_path)

        old_graph = generate_graph_from_text(old_text)
        new_graph = generate_graph_from_text(new_text)

        parse_and_store_graph(old_graph, "old")
        parse_and_store_graph(new_graph, "new")

        return redirect(url_for("compare"))
    return render_template("index.html")

@app.route("/compare")
def compare():
    return render_template("compare.html")

@app.route("/graph_data/<version>")
def get_graph_data(version):
    G = graphs.get(version)
    if not G:
        return jsonify({"nodes": [], "edges": []})

    nodes = [{"id": node, "label": data["label"], "group": data.get("group", "Entity")} for node, data in G.nodes(data=True)]
    edges = [{"from": u, "to": v, "label": data.get("label", "")} for u, v, data in G.edges(data=True)]

    return jsonify({"nodes": nodes, "edges": edges})
