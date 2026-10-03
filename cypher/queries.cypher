// Each query starts with a line "// ### Title". Used by src/run_queries.py and also fine to paste in Neo4j Browser.

// ### Node counts per label
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS nodes ORDER BY nodes DESC;

// ### Relationship counts per type
MATCH ()-[r]->() RETURN type(r) AS relationship, count(*) AS total ORDER BY total DESC;

// ### Top 10 most-rated movies
MATCH (m:Movie)<-[r:RATED]-()
RETURN m.title AS movie, m.year AS year, count(r) AS ratings
ORDER BY ratings DESC LIMIT 10;

// ### Top 10 highest-rated movies (min 30 ratings)
MATCH (m:Movie)<-[r:RATED]-()
WITH m, count(r) AS n, avg(r.rating) AS avg_rating
WHERE n >= 30
RETURN m.title AS movie, round(avg_rating, 2) AS avg_rating, n AS ratings
ORDER BY avg_rating DESC LIMIT 10;

// ### Most prolific actors
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
RETURN p.name AS actor, count(m) AS movies
ORDER BY movies DESC LIMIT 10;

// ### Frequent co-star pairs
MATCH (a:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(b:Person)
WHERE a.person_id < b.person_id
RETURN a.name AS actor_1, b.name AS actor_2, count(m) AS movies_together, collect(m.title)[..3] AS sample_movies
ORDER BY movies_together DESC LIMIT 10;

// ### Director-actor collaborations
MATCH (d:Person)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a:Person)
WHERE d <> a
RETURN d.name AS director, a.name AS actor, count(m) AS films
ORDER BY films DESC LIMIT 10;

// ### Shortest path between two people (Bacon-number style)
MATCH (a:Person {person_id: 'P0001'}), (b:Person {person_id: 'P0100'})
MATCH path = shortestPath((a)-[:ACTED_IN*..12]-(b))
RETURN length(path) / 2 AS degrees_of_separation,
       [n IN nodes(path) | coalesce(n.name, n.title)] AS chain;

// ### Genre popularity and average rating
MATCH (g:Genre)<-[:IN_GENRE]-(m:Movie)<-[r:RATED]-(:User)
RETURN g.name AS genre, count(DISTINCT m) AS movies, count(r) AS ratings, round(avg(r.rating), 2) AS avg_rating
ORDER BY avg_rating DESC;

// ### Collaborative filtering: recommendations for user U0001
MATCH (me:User {user_id: 'U0001'})-[r1:RATED]->(m:Movie)<-[r2:RATED]-(other:User)
WHERE r1.rating >= 4 AND r2.rating >= 4 AND other <> me
WITH me, other, count(m) AS shared_liked
WHERE shared_liked >= 3
MATCH (other)-[r3:RATED]->(rec:Movie)
WHERE r3.rating >= 4 AND NOT (me)-[:RATED]->(rec)
RETURN rec.title AS recommended, count(DISTINCT other) AS supporters, round(avg(r3.rating), 2) AS avg_rating_by_peers
ORDER BY supporters DESC, avg_rating_by_peers DESC LIMIT 10;

// ### Users most similar to U0001 (Jaccard similarity on liked movies)
MATCH (me:User {user_id: 'U0001'})-[r1:RATED]->(m:Movie) WHERE r1.rating >= 4
WITH me, collect(m) AS mine
MATCH (other:User)-[r2:RATED]->(m2:Movie) WHERE other <> me AND r2.rating >= 4
WITH mine, other, collect(m2) AS theirs
WITH other, mine, theirs, size([x IN mine WHERE x IN theirs]) AS inter
WHERE inter > 0
RETURN other.user_id AS user_id, other.name AS similar_user, inter AS shared_liked,
       round(toFloat(inter) / (size(mine) + size(theirs) - inter), 3) AS jaccard
ORDER BY jaccard DESC LIMIT 10;

// ### Content-based: movies similar to M0001 (shared genres and actors)
MATCH (m:Movie {movie_id: 'M0001'})
MATCH (m)-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(sim:Movie)
WHERE sim <> m
WITH m, sim, count(g) AS shared_genres
OPTIONAL MATCH (m)<-[:ACTED_IN]-(p:Person)-[:ACTED_IN]->(sim)
WITH sim, shared_genres, count(p) AS shared_actors
RETURN sim.title AS similar_movie, shared_genres, shared_actors, shared_genres * 2 + shared_actors * 3 AS score
ORDER BY score DESC LIMIT 10;

// ### Most influential users (followers)
MATCH (u:User)<-[f:FOLLOWS]-()
RETURN u.user_id AS user_id, u.name AS name, count(f) AS followers
ORDER BY followers DESC LIMIT 10;

// ### Social recommendations: what friends (and friends-of-friends) of U0001 liked
MATCH (me:User {user_id: 'U0001'})-[:FOLLOWS*1..2]->(friend:User)-[r:RATED]->(m:Movie)
WHERE r.rating >= 4 AND friend <> me AND NOT (me)-[:RATED]->(m)
RETURN m.title AS movie, count(DISTINCT friend) AS friends_who_liked, round(avg(r.rating), 2) AS avg_rating
ORDER BY friends_who_liked DESC, avg_rating DESC LIMIT 10;

// ### Taste communities: fans per favourite genre
MATCH (u:User) UNWIND u.favorite_genres AS genre
RETURN genre, count(*) AS fans ORDER BY fans DESC;

// ### Rating activity per year
MATCH ()-[r:RATED]->()
RETURN r.rated_at.year AS year, count(*) AS ratings, round(avg(r.rating), 2) AS avg_rating
ORDER BY year;

// ### Average rating by movie decade
MATCH (m:Movie)<-[r:RATED]-()
RETURN (m.year / 10) * 10 AS decade, count(DISTINCT m) AS movies, round(avg(r.rating), 2) AS avg_rating
ORDER BY decade;

// ### People who both act and direct
MATCH (p:Person)-[:DIRECTED]->(d:Movie)
WHERE (p)-[:ACTED_IN]->()
RETURN p.name AS person, count(DISTINCT d) AS films_directed, size([(p)-[:ACTED_IN]->(x) | x]) AS films_acted
ORDER BY films_directed DESC, films_acted DESC LIMIT 10;

// ### Does a bigger budget mean a better rating? (budget bands, min 30 ratings)
MATCH (m:Movie)<-[r:RATED]-()
WITH m, avg(r.rating) AS a, count(r) AS n WHERE n >= 30
RETURN toInteger(m.budget_musd / 50) * 50 AS budget_band_musd, count(m) AS movies, round(avg(a), 2) AS avg_rating
ORDER BY budget_band_musd;

// ### Hidden gems: high rating but few viewers
MATCH (m:Movie)<-[r:RATED]-()
WITH m, count(r) AS n, avg(r.rating) AS a
WHERE n < 100 AND a >= 3.4
RETURN m.title AS movie, n AS ratings, round(a, 2) AS avg_rating
ORDER BY avg_rating DESC, n ASC LIMIT 10;
