from neo4j import GraphDatabase

# TODO: Set up authentication for the Neo4j database to be extracted from environment variables
class Neo4jConnector:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_corpus_node(self, corpus_id, title, text):
        with self.driver.session() as session:
            session.execute_write(self._create_and_return_corpus, corpus_id, title, text)

    def create_correlation_relationship(self, corpus_id1, corpus_id2, correlation):
        with self.driver.session() as session:
            session.execute_write(self._create_and_return_relationship, corpus_id1, corpus_id2, correlation)

    def query_by_title(self, title):
        with self.driver.session() as session:
            result = session.execute_read(self._query_by_title, title)
            return result

    @staticmethod
    def _create_and_return_corpus(tx, corpus_id, title, text):
        query = (
            "CREATE (c:Corpus {id: $corpus_id, title: $title, text: $text}) "
            "RETURN c"
        )
        result = tx.run(query, corpus_id=corpus_id, title=title, text=text)
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

    @staticmethod
    def _query_by_title(tx, title):
        query = (
            "MATCH (c:Corpus {title: $title}) "
            "RETURN c"
        )
        result = tx.run(query, title=title)
        return [record["c"] for record in result]
