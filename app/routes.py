import os
from flask import Blueprint, request, render_template
from app.rag_engine import create_vectorstore_from_pdf, get_answer
from app.graph_engine import extract_ae_triplets, build_graph, visualize_graph

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        file = request.files["doc"]
        filepath = os.path.join("data/uploaded_docs", file.filename)
        file.save(filepath)
        create_vectorstore_from_pdf(filepath)

        query = request.form["query"]
        result = get_answer(query)

        triplets = extract_ae_triplets(result)
        graph = build_graph(triplets)
        visualize_graph(graph, "app/static/graph.html")

    return render_template("index.html", result=result)