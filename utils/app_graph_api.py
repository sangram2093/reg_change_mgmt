from flask import Flask, jsonify
from neo4j import GraphDatabase
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Neo4j credentials from environment or fallback
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def fetch_graph_data(version):
    with driver.session() as session:
        query = (
            "MATCH (a:Entity {version: $version})-[r:ACTION]->(b:Entity {version: $version}) "
            "RETURN a, r, b"
        )
        result = session.run(query, version=version)

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

            verb = r.get("verb", "ACTION")
            confidence = round(r.get("confidence_score", 1.0), 2)
            optionality = r.get("optionality", "N/A")
            property_of_object = r.get("property_of_object", "N/A")
            threshold = r.get("threshold", "N/A")

            edge_label = f"{verb} ({confidence})"
            edge_title = f"Optionality: {optionality}\nProperty: {property_of_object}\nThreshold: {threshold}"

            edge = {
                "from": a_id,
                "to": b_id,
                "label": edge_label,
                "title": edge_title
            }
            edges.append(edge)

        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }

@app.route("/graph_data/<version>")
def get_graph_data(version):
    if version not in ["old", "new"]:
        return jsonify({"error": "Invalid version"}), 400
    data = fetch_graph_data(version)
    return jsonify(data)
