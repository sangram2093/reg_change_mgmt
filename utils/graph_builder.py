from neo4j import GraphDatabase
import json
import uuid

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "your_password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def create_graph(data_json):
    data = json.loads(data_json)

    with driver.session() as session:
        for entity in data.get("entities", []):
            session.run("""
                MERGE (e:Entity {id: $id})
                SET e.name = $name, e.type = $type
            """, id=entity["id"], name=entity["name"], type=entity.get("type", "unknown"))

        for rel in data.get("relationships", []):
            session.run("""
                MATCH (s:Entity {id: $subject_id})
                MATCH (o:Entity {id: $object_id})
                MERGE (s)-[:ACTION {name: $verb}]->(o)
            """, subject_id=rel["subject_id"], verb=rel["verb"], object_id=rel["object_id"])

