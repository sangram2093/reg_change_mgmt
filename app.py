from flask import Flask, request, render_template
import os
import json
from dotenv import load_dotenv
from utils.pdf_reader import extract_text_from_pdf
from utils.vertex_llm import init_vertexai, get_summary_entities
from utils.graph_builder import create_graph, get_graph_differences

load_dotenv()
app = Flask(__name__)
os.makedirs("logs", exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/compare", methods=["POST"])
def compare_graphs():
    old_pdf = request.form.get("old_pdf_path")
    new_pdf = request.form.get("new_pdf_path")

    init_vertexai()

    old_text = extract_text_from_pdf(old_pdf)
    new_text = extract_text_from_pdf(new_pdf)

    old_data = get_summary_entities(old_text, version="old")
    new_data = get_summary_entities(new_text, version="new")

    create_graph(old_data, version="old")
    create_graph(new_data, version="new")

    delta = get_graph_differences()

    return render_template("compare.html", delta_summary=json.dumps(delta, indent=2))

if __name__ == "__main__":
    app.run(debug=True)
