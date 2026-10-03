"""Run the Cypher queries in cypher/queries.cypher and print nice tables.
Usage:
  python src/run_queries.py --list        # list query numbers and titles
  python src/run_queries.py               # run all
  python src/run_queries.py --only 3 10   # run selected ones
"""
import argparse, os, re, sys
from neo4j import GraphDatabase
import config

QUERY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cypher", "queries.cypher")


def parse_queries(path):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"^// ### ", text, flags=re.M)[1:]
    out = []
    for p in parts:
        title, _, body = p.partition("\n")
        body = "\n".join(l for l in body.splitlines() if not l.strip().startswith("//")).strip().rstrip(";")
        out.append((title.strip(), body))
    return out


def table(records, keys, limit=15):
    if not records:
        print("  (no rows)"); return
    rows = [[str(r[k])[:48] for k in keys] for r in records[:limit]]
    widths = [max(len(k), *(len(r[i]) for r in rows)) for i, k in enumerate(keys)]
    print("  " + " | ".join(k.ljust(w) for k, w in zip(keys, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for r in rows:
        print("  " + " | ".join(c.ljust(w) for c, w in zip(r, widths)))
    if len(records) > limit:
        print(f"  ... {len(records) - limit} more rows")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", nargs="*", type=int)
    a = ap.parse_args()
    queries = parse_queries(QUERY_FILE)
    if a.list:
        for i, (t, _) in enumerate(queries, 1): print(f"{i:>2}. {t}")
        return
    driver = GraphDatabase.driver(config.URI, auth=(config.USER, config.PASSWORD))
    try:
        driver.verify_connectivity()
    except Exception as e:
        sys.exit(f"Cannot connect to Neo4j: {e}")
    with driver, driver.session() as s:
        for i, (title, cy) in enumerate(queries, 1):
            if a.only and i not in a.only: continue
            print(f"\n[{i}] {title}")
            try:
                res = s.run(cy)
                keys = res.keys(); recs = list(res)
                table(recs, keys)
            except Exception as e:
                print("  ERROR:", str(e).splitlines()[0])


if __name__ == "__main__":
    main()
