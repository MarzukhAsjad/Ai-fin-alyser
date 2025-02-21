from neo4j import GraphDatabase

class Neo4jConnector:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_corpus_node(self, corpus_id, text):
        with self.driver.session() as session:
            session.execute_write(self._create_and_return_corpus, corpus_id, text)

    def create_correlation_relationship(self, corpus_id1, corpus_id2, correlation):
        with self.driver.session() as session:
            session.execute_write(self._create_and_return_relationship, corpus_id1, corpus_id2, correlation)

    @staticmethod
    def _create_and_return_corpus(tx, corpus_id, text):
        query = (
            "CREATE (c:Corpus {id: $corpus_id, text: $text}) "
            "RETURN c"
        )
        result = tx.run(query, corpus_id=corpus_id, text=text)
        return result.single()

    @staticmethod
    def _create_and_return_relationship(tx, corpus_id1, corpus_id2, correlation):
        query = (
            "MATCH (c1:Corpus {id: $corpus_id1}), (c2:Corpus {id: $corpus_id2}) "
            "CREATE (c1)-[r:CORRELATED {correlation: $correlation}]->(c2) "
            "RETURN r"
        )
        result = tx.run(query, corpus_id1=corpus_id1, corpus_id2=corpus_id2, correlation=correlation)
        return result.single()
