import os
from flask import Blueprint, request, render_template
from app.rag_engine import create_vectorstore_from_pdf, get_answer
from app.graph_engine import extract_ae_triplets, build_graph, visualize_graph

main = Blueprint("main", __name__)
pdf_directory = "data/uploaded_docs"

@main.route("/", methods=["GET", "POST"])
def index():
    result = None

    # Step 1: Load all PDFs into vectorstore (only once)
    if not os.path.exists("vectorstore/index.faiss"):
        for filename in os.listdir(pdf_directory):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(pdf_directory, filename)
                create_vectorstore_from_pdf(pdf_path)

    # Step 2: Handle user question
    if request.method == "POST":
        query = request.form["query"]
        result = get_answer(query)

        triplets = extract_ae_triplets(result)
        graph = build_graph(triplets)
        visualize_graph(graph, "app/static/graph.html")

    return render_template("index.html", result=result)
