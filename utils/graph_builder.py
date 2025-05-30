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
        for rel in data.get("relationships", []):
            subj = rel["subject"]
            verb = rel["verb"]
            obj = rel["object"]

            subj_id = str(uuid.uuid4())
            obj_id = str(uuid.uuid4())

            session.run("""
                MERGE (s:Entity {id: $subj_id, name: $subj})
                MERGE (o:Entity {id: $obj_id, name: $obj})
                MERGE (s)-[:ACTION {name: $verb}]->(o)
            """, subj=subj, verb=verb, obj=obj, subj_id=subj_id, obj_id=obj_id)
