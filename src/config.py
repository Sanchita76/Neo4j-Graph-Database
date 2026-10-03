import os
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_pass_123")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
