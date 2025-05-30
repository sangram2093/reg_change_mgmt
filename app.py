from flask import Flask, request
import os
from utils.pdf_reader import extract_text_from_pdf
from utils.vertex_llm import init_vertexai, get_summary_entities
from utils.graph_builder import create_graph

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return '''
        <h2>Regulatory Change Analyzer</h2>
        <form action="/analyze" method="post">
            PDF File Path: <input type="text" name="pdf_path" required>
            <input type="submit" value="Analyze">
        </form>
    '''

@app.route("/analyze", methods=["POST"])
def analyze():
    pdf_path = request.form.get("pdf_path")

    if not os.path.isfile(pdf_path):
        return f"<h3>Error: File does not exist - {pdf_path}</h3>"

    init_vertexai()
    text = extract_text_from_pdf(pdf_path)
    llm_output = get_summary_entities(text)
    create_graph(llm_output)

    return f"<h3>Graph created successfully for: {pdf_path}</h3><pre>{llm_output}</pre>"

if __name__ == "__main__":
    app.run(debug=True)
