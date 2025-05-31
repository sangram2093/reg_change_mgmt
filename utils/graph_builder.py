from neo4j import GraphDatabase
import json

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "your_password"  # Replace with your actual Neo4j password

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def create_graph(data_json, version):
    data = json.loads(data_json)
    entity_ids = set()

    with driver.session() as session:
        print(f"\n--- Inserting Entities for version: {version} ---")
        for entity in data.get("entities", []):
            entity_id = entity["id"].strip()
            entity_ids.add(entity_id)

            session.run("""
                MERGE (e:Entity {id: $id})
                SET e.name = $name, e.type = $type, e.version = $version
            """, id=entity_id, name=entity["name"].strip(), type=entity.get("type", "unknown"), version=version)
        
        print(f"✔ Inserted {len(entity_ids)} entities.")

        print(f"\n--- Inserting Relationships for version: {version} ---")
        relationship_count = 0
        for rel in data.get("relationships", []):
            subject_id = rel["subject_id"].strip()
            object_id = rel["object_id"].strip()

            if subject_id not in entity_ids or object_id not in entity_ids:
                print(f"⚠ Skipping relationship due to missing entities: {subject_id} -> {rel['verb']} -> {object_id}")
                continue

            session.run("""
                MERGE (s:Entity {id: $subject_id})
                  ON CREATE SET s.version = $version
                MERGE (o:Entity {id: $object_id})
                  ON CREATE SET o.version = $version
                MERGE (s)-[:ACTION {
                    name: $verb,
                    confidence_score: $score
                }]->(o)
            """, subject_id=subject_id, object_id=object_id, verb=rel["verb"].strip(),
                 score=rel.get("confidence_score", 1.0), version=version)
            relationship_count += 1

        print(f"✔ Inserted {relationship_count} relationships.\n")


def get_graph_differences():
    with driver.session() as session:
        print("\n--- Computing Graph Delta ---")
        result = session.run("""
            MATCH (a:Entity {version: 'new'})-[r:ACTION]->(b:Entity {version: 'new'})
            WHERE NOT EXISTS {
              MATCH (a_old:Entity {version: 'old'})-[r_old:ACTION]->(b_old:Entity {version: 'old'})
              WHERE a_old.name = a.name AND b_old.name = b.name AND r_old.name = r.name
            }
            RETURN a.name AS subject, r.name AS verb, b.name AS object
        """)
        delta = [dict(record) for record in result]
        print(f"✔ Found {len(delta)} delta relationships.\n")
        return delta
