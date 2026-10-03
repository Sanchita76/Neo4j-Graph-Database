"""Load the CSV files into Neo4j using the official Python driver (batched UNWIND).
Usage: python src/load_graph.py [--wipe]
"""
import argparse, csv, os, sys
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import config

CONSTRAINTS = [
    "CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.movie_id IS UNIQUE",
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.person_id IS UNIQUE",
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
    "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
    "CREATE INDEX movie_title IF NOT EXISTS FOR (m:Movie) ON (m.title)",
    "CREATE INDEX movie_year IF NOT EXISTS FOR (m:Movie) ON (m.year)",
]

# (csv file, cypher using $rows, converter)
STEPS = [
    ("genres.csv", "UNWIND $rows AS r MERGE (:Genre {name: r.name})", lambda r: r),
    ("persons.csv", "UNWIND $rows AS r MERGE (p:Person {person_id: r.person_id}) "
                    "SET p.name = r.name, p.born = toInteger(r.born), p.country = r.country",
     lambda r: r),
    ("movies.csv", "UNWIND $rows AS r MERGE (m:Movie {movie_id: r.movie_id}) "
                   "SET m.title = r.title, m.year = toInteger(r.year), m.runtime = toInteger(r.runtime), "
                   "m.budget_musd = toFloat(r.budget_musd)", lambda r: r),
    ("users.csv", "UNWIND $rows AS r MERGE (u:User {user_id: r.user_id}) "
                  "SET u.name = r.name, u.age = toInteger(r.age), u.country = r.country, "
                  "u.favorite_genres = split(r.favorite_genres, '|')", lambda r: r),
    ("in_genre.csv", "UNWIND $rows AS r MATCH (m:Movie {movie_id: r.movie_id}), (g:Genre {name: r.genre}) "
                     "MERGE (m)-[:IN_GENRE]->(g)", lambda r: r),
    ("acted_in.csv", "UNWIND $rows AS r MATCH (p:Person {person_id: r.person_id}), (m:Movie {movie_id: r.movie_id}) "
                     "MERGE (p)-[a:ACTED_IN]->(m) SET a.role = r.role", lambda r: r),
    ("directed.csv", "UNWIND $rows AS r MATCH (p:Person {person_id: r.person_id}), (m:Movie {movie_id: r.movie_id}) "
                     "MERGE (p)-[:DIRECTED]->(m)", lambda r: r),
    ("rated.csv", "UNWIND $rows AS r MATCH (u:User {user_id: r.user_id}), (m:Movie {movie_id: r.movie_id}) "
                  "MERGE (u)-[x:RATED]->(m) SET x.rating = toFloat(r.rating), x.rated_at = date(r.rated_at)",
     lambda r: r),
    ("follows.csv", "UNWIND $rows AS r MATCH (a:User {user_id: r.follower}), (b:User {user_id: r.followed}) "
                    "MERGE (a)-[:FOLLOWS]->(b)", lambda r: r),
]


def read_csv(name):
    with open(os.path.join(config.DATA_DIR, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wipe", action="store_true", help="delete everything first")
    ap.add_argument("--batch", type=int, default=2000)
    a = ap.parse_args()
    try:
        driver = GraphDatabase.driver(config.URI, auth=(config.USER, config.PASSWORD))
        driver.verify_connectivity()
    except (ServiceUnavailable, AuthError) as e:
        sys.exit(f"Cannot connect to Neo4j at {config.URI}: {e}\nIs 'docker compose up -d' running (wait ~30s)?")
    if not os.path.exists(os.path.join(config.DATA_DIR, "movies.csv")):
        sys.exit("No CSV files found. Run: python src/generate_data.py")
    with driver, driver.session() as s:
        if a.wipe:
            s.run("MATCH (n) DETACH DELETE n").consume()
            print("Database wiped")
        for c in CONSTRAINTS:
            s.run(c).consume()
        for fname, cypher, _ in STEPS:
            rows = read_csv(fname)
            for i in range(0, len(rows), a.batch):
                s.run(cypher, rows=rows[i:i + a.batch]).consume()
            print(f"Loaded {fname:<14} ({len(rows)} rows)")
        print("\nGraph summary:")
        for rec in s.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC"):
            print(f"  {rec['label']:<8} {rec['n']}")
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
        print(f"  relationships: {rels}")


if __name__ == "__main__":
    main()
