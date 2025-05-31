from neo4j import GraphDatabase
import json

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "your_password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def create_graph(data_json, version):
    data = json.loads(data_json)
    with driver.session() as session:
        for entity in data.get("entities", []):
            session.run("""
                MERGE (e:Entity {id: $id})
                SET e.name = $name, e.type = $type, e.version = $version
            """, id=entity["id"], name=entity["name"], type=entity.get("type", "unknown"), version=version)

        for rel in data.get("relationships", []):
            session.run("""
                MATCH (s:Entity {id: $subject_id, version: $version})
                MATCH (o:Entity {id: $object_id, version: $version})
                MERGE (s)-[:ACTION {name: $verb, confidence_score: $score}]->(o)
            """, subject_id=rel["subject_id"], verb=rel["verb"], object_id=rel["object_id"], score=rel.get("confidence_score", 1.0), version=version)

def get_graph_differences():
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Entity)-[r:ACTION]->(b:Entity)
            WHERE a.version = 'new' AND NOT EXISTS {
              MATCH (a_old:Entity)-[r_old:ACTION]->(b_old:Entity)
              WHERE a_old.name = a.name AND b_old.name = b.name AND r_old.name = r.name
              AND a_old.version = 'old' AND b_old.version = 'old'
            }
            RETURN a.name AS subject, r.name AS verb, b.name AS object
        """)
        return [dict(record) for record in result]
