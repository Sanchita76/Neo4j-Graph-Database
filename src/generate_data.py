"""Generate a synthetic movie-recommendation graph dataset as CSV files in ./data.
Users have genre tastes, so recommendations found by the Cypher queries are meaningful.
Usage: python src/generate_data.py [--users 1000] [--movies 400] [--persons 600]
"""
import argparse, csv, os, random
from datetime import date, timedelta
from config import DATA_DIR

GENRES = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Fantasy",
          "Horror", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western", "Musical"]
FIRST = ["Alex", "Maria", "John", "Priya", "Liam", "Sofia", "Chen", "Aisha", "Noah", "Emma", "Ravi", "Olga",
         "Diego", "Mei", "Omar", "Anna", "Kenji", "Lucas", "Zara", "Ethan", "Nina", "Arjun", "Isla", "Tariq"]
LAST = ["Smith", "Garcia", "Kumar", "Chen", "Muller", "Rossi", "Khan", "Silva", "Ivanov", "Tanaka", "Brown",
        "Nguyen", "Lopez", "Sen", "Dubois", "Okafor", "Kim", "Novak", "Haddad", "Larsen"]
ADJ = ["Silent", "Broken", "Golden", "Last", "Hidden", "Crimson", "Eternal", "Midnight", "Lost", "Burning",
       "Frozen", "Wild", "Secret", "Electric", "Hollow", "Distant"]
NOUN = ["Horizon", "Empire", "Garden", "Protocol", "Night", "River", "Code", "Kingdom", "Echo", "Storm",
        "Mirror", "Journey", "Legacy", "Signal", "Harbor", "Frontier"]
COUNTRIES = ["USA", "UK", "India", "France", "Germany", "Japan", "Brazil", "Canada", "Australia", "Spain"]
ROLES = ["Lead", "Supporting", "Cameo", "Villain", "Sidekick"]


def write(name, header, rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print(f"  {name}: {len(rows)} rows")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=1000)
    ap.add_argument("--movies", type=int, default=400)
    ap.add_argument("--persons", type=int, default=600)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    r = random.Random(a.seed)

    # persons
    persons = [(f"P{i:04d}", f"{r.choice(FIRST)} {r.choice(LAST)} {i}", r.randint(1950, 2000), r.choice(COUNTRIES))
               for i in range(1, a.persons + 1)]
    person_ids = [p[0] for p in persons]

    # movies + genres + cast
    movies, in_genre, acted, directed = [], [], [], []
    titles = set()
    for i in range(1, a.movies + 1):
        while True:
            t = f"The {r.choice(ADJ)} {r.choice(NOUN)}"
            if t in titles: t += f" {r.choice(['II','III','Returns','Origins','Reborn'])}"
            if t not in titles: titles.add(t); break
        mid = f"M{i:04d}"
        movies.append((mid, t, r.randint(1985, 2024), r.randint(80, 175), round(r.uniform(2, 250), 1)))
        for g in r.sample(GENRES, r.choice([1, 2, 2, 3])):
            in_genre.append((mid, g))
        directed.append((r.choice(person_ids), mid))
        for pid in r.sample(person_ids, r.randint(3, 7)):
            acted.append((pid, mid, r.choice(ROLES)))

    # users with favourite genres
    users, rated, follows = [], [], []
    by_genre = {g: [] for g in GENRES}
    for mid, g in in_genre: by_genre[g].append(mid)
    movie_genres = {}
    for mid, g in in_genre: movie_genres.setdefault(mid, set()).add(g)
    all_mids = [m[0] for m in movies]
    for i in range(1, a.users + 1):
        uid = f"U{i:04d}"
        favs = r.sample(GENRES, 2)
        users.append((uid, f"{r.choice(FIRST)} {r.choice(LAST)}", r.randint(16, 70), r.choice(COUNTRIES), "|".join(favs)))
        pool = set()
        for g in favs: pool.update(r.sample(by_genre[g], min(len(by_genre[g]), 22)))
        pool.update(r.sample(all_mids, 8))
        for mid in pool:
            base = 4.0 if movie_genres[mid] & set(favs) else 2.6
            rating = min(5, max(1, round(r.gauss(base, 0.8) * 2) / 2))   # half-star steps
            d = date(2019, 1, 1) + timedelta(days=r.randint(0, 2000))
            rated.append((uid, mid, rating, d.isoformat()))
    uids = [u[0] for u in users]
    for u in uids:
        for other in r.sample(uids, r.randint(2, 15)):
            if other != u: follows.append((u, other))

    print("Writing CSV files to", os.path.abspath(DATA_DIR))
    write("genres.csv", ["name"], [(g,) for g in GENRES])
    write("persons.csv", ["person_id", "name", "born", "country"], persons)
    write("movies.csv", ["movie_id", "title", "year", "runtime", "budget_musd"], movies)
    write("users.csv", ["user_id", "name", "age", "country", "favorite_genres"], users)
    write("in_genre.csv", ["movie_id", "genre"], in_genre)
    write("acted_in.csv", ["person_id", "movie_id", "role"], acted)
    write("directed.csv", ["person_id", "movie_id"], directed)
    write("rated.csv", ["user_id", "movie_id", "rating", "rated_at"], rated)
    write("follows.csv", ["follower", "followed"], follows)


if __name__ == "__main__":
    main()
