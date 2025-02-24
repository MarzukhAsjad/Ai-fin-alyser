from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Neo4jConnector:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def test_connection(self):
        with self.driver.session() as session:
            result = session.run("RETURN 1")
            return result.single()[0] == 1

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

    def query_all_correlations(self):
        with self.driver.session() as session:
            result = session.execute_read(self._query_all_correlations)
            return result
        
    def query_pairwise_causal(self):
        with self.driver.session() as session:
            return session.execute_read(self._query_pairwise_causal)

    def query_highest_correlation(self, n: int = 1):
        with self.driver.session() as session:
            result = session.execute_read(self._query_highest_correlation, int(n))
            return result

    def clear_database(self):
        with self.driver.session() as session:
            session.execute_write(self._clear_database)

    def query_all_corpora(self):
        with self.driver.session() as session:
            result = session.execute_read(self._query_all_corpora)
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
            "MATCH (c1:Corpus {id: $corpus_id1}) "
            "MATCH (c2:Corpus {id: $corpus_id2}) "
            "CREATE (c1)-[r:CORRELATED {correlation: $correlation}]->(c2) "
            "RETURN r"
        )
        try:
            result = tx.run(query, corpus_id1=corpus_id1, corpus_id2=corpus_id2, correlation=correlation)
            record = result.single()
            return record
        except Exception as e:
            print(f"ERROR in _create_and_return_relationship: {e} for parameters corpus_id1={corpus_id1}, corpus_id2={corpus_id2}, correlation={correlation}")
            raise

    @staticmethod
    def _query_by_title(tx, title):
        query = (
            "MATCH (c:Corpus {title: $title}) "
            "RETURN c"
        )
        result = tx.run(query, title=title)
        return [record["c"] for record in result]

    @staticmethod
    def _query_all_correlations(tx):
        query = (
            "MATCH (c1:Corpus)-[r:CORRELATED]->(c2:Corpus) "
            "RETURN c1.id AS id1, c1.title AS title1, c2.id AS id2, c2.title AS title2, r.correlation AS correlation"
        )
        result = tx.run(query)
        return [record.data() for record in result]

    @staticmethod
    def _query_pairwise_causal(tx):
        query = (
            "MATCH (c:Corpus)-[r:CORRELATED]->(other:Corpus) " 
            "WITH c, r, other ORDER BY r.correlation DESC " 
            "WITH c, head(collect({otherTitle: other.title, correlation: r.correlation})) AS bestRel " 
            "RETURN c.title AS corpusTitle, bestRel.otherTitle AS highestCorrelationCorpus, bestRel.correlation AS highestCorrelation"
        )
        result = tx.run(query)
        return [record.data() for record in result]

    @staticmethod
    def _query_highest_correlation(tx, n: int):
        query = (
            "MATCH (c1:Corpus)-[r:CORRELATED]->(c2:Corpus) "
            "RETURN c1.title AS corpus1, c2.title AS corpus2, r.correlation AS correlation "
            "ORDER BY r.correlation DESC "
            "LIMIT $n"
        )
        result = tx.run(query, n=n)
        return [record.data() for record in result]

    @staticmethod
    def _clear_database(tx):
        query = "MATCH (n) DETACH DELETE n"
        tx.run(query)

    @staticmethod
    def _query_all_corpora(tx):
        query = (
            "MATCH (c:Corpus) "
            "RETURN c.id AS id, c.title AS title, c.text AS text"
        )
        result = tx.run(query)
        return [record.data() for record in result]
