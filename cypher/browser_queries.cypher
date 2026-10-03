// Paste these one at a time into Neo4j Browser (http://localhost:7474) to SEE the graph visually.

// 1. Schema of the graph
CALL db.schema.visualization();

// 2. A user and what they rated highly
MATCH p = (u:User {user_id: 'U0001'})-[r:RATED]->(m:Movie) WHERE r.rating >= 4.5 RETURN p LIMIT 25;

// 3. A movie with its cast, director and genres
MATCH (m:Movie {movie_id: 'M0001'})
OPTIONAL MATCH a = (m)<-[:ACTED_IN]-(:Person)
OPTIONAL MATCH d = (m)<-[:DIRECTED]-(:Person)
OPTIONAL MATCH g = (m)-[:IN_GENRE]->(:Genre)
RETURN m, a, d, g;

// 4. Co-actor network around one actor (2 hops)
MATCH p = (a:Person {person_id: 'P0001'})-[:ACTED_IN]->(:Movie)<-[:ACTED_IN]-(:Person) RETURN p LIMIT 50;

// 5. Social graph around a user
MATCH p = (u:User {user_id: 'U0001'})-[:FOLLOWS*1..2]->(:User) RETURN p LIMIT 60;

// 6. Shortest path drawn as a graph
MATCH (a:Person {person_id: 'P0001'}), (b:Person {person_id: 'P0100'})
RETURN shortestPath((a)-[:ACTED_IN*..12]-(b)) AS path;
