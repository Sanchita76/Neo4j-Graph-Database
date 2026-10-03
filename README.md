# Project 2 - Neo4j Graph Database + Cypher Queries with Python

**What you get:** a Neo4j database in Docker, a synthetic *movie recommendation graph* (users, movies, actors,
directors, genres, ratings, follows - ~1,000 users, 400 movies, ~50k ratings), Python code that generates/loads it,
and 20 Cypher queries (aggregation, shortest path, collaborative filtering, similarity, social recommendations).

```
02-neo4j-graph-database/
├── docker-compose.yml       # Neo4j 5 (Browser on :7474, Bolt on :7687)
├── requirements.txt
├── src/
│   ├── config.py            # connection settings (URI / user / password)
│   ├── generate_data.py     # creates CSV files in data/
│   ├── load_graph.py        # loads CSVs into Neo4j with the Python driver
│   └── run_queries.py       # runs cypher/queries.cypher, prints tables
├── cypher/
│   ├── queries.cypher       # 20 analytical queries
│   └── browser_queries.cypher  # visual queries to paste in Neo4j Browser
└── data/                    # generated CSVs
```

## Graph model
```
(Person)-[:ACTED_IN {role}]->(Movie)<-[:DIRECTED]-(Person)
(Movie)-[:IN_GENRE]->(Genre)
(User)-[:RATED {rating, rated_at}]->(Movie)
(User)-[:FOLLOWS]->(User)
```

## 1. Install (one time)
* **Docker Desktop** - https://www.docker.com/products/docker-desktop
* **Python 3.9+** - https://www.python.org/downloads (Windows: tick "Add Python to PATH")

## 2. Run it
```bash
docker compose up -d                 # starts Neo4j (wait ~30 seconds)
python -m venv venv
#   Windows: venv\Scripts\activate       Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

python src/generate_data.py          # (re)creates CSVs in data/  (already included, optional)
python src/load_graph.py --wipe      # loads everything into Neo4j
python src/run_queries.py --list     # see all queries
python src/run_queries.py            # run all queries (or: --only 10 11)
```

## 3. Explore visually
Open **http://localhost:7474**, login: user `neo4j`, password `neo4j_pass_123`
(connect URL `bolt://localhost:7687`). Paste queries from `cypher/browser_queries.cypher` to see the graph.

## 4. What the main queries teach
| # | Concept | Query |
|---|---|---|
| 3-5 | aggregation | most-rated movies, top rated, prolific actors |
| 8 | **shortest path** | degrees of separation between two actors |
| 10 | **collaborative filtering** | "users like you also liked..." for user U0001 |
| 11 | **Jaccard similarity** | most similar users |
| 12 | **content-based recommendation** | similar movies by shared genre/actors |
| 13-14 | **social graph** | influencers, friends-of-friends recommendations |

## 5. Calling Cypher from your own Python code
```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neo4j_pass_123"))
with driver.session() as s:
    for rec in s.run("MATCH (m:Movie) WHERE m.year > $y RETURN m.title AS t LIMIT 5", y=2015):
        print(rec["t"])
```
Always pass values as **parameters** (`$y`) instead of string formatting - faster and safe from injection.

## 6. Using a real Kaggle dataset instead (optional)
Download e.g. "The Movies Dataset" (`rounakbanik/the-movies-dataset`) or "MovieLens", convert with pandas to CSVs with the
same headers as in `data/`, then run `load_graph.py`. The loader only needs the 9 CSV files.

## 7. Stop / clean up
```bash
docker compose down        # stop
docker compose down -v     # stop and delete the database
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `Cannot connect to Neo4j` | wait 30-60 s after `docker compose up -d`; check `docker compose logs neo4j` |
| `AuthError` | password must match `NEO4J_AUTH` in docker-compose.yml (default `neo4j_pass_123`); if you changed it, remove the volume: `docker compose down -v` |
| Empty query results | you forgot `python src/load_graph.py` |
| Port 7474/7687 busy | change the left side of the `ports:` mapping and set `NEO4J_URI` |

Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` environment variables to point to a different server (e.g. Neo4j Aura).
> Queries were syntax-checked by review, not executed in the authoring sandbox (no Neo4j available there). If one errors,
> `run_queries.py` prints the error and continues with the others.
