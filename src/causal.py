from .nlp_processor import compare_corpora
from .neo4j_connector import Neo4jConnector

def store_correlation_scores(corpus: list, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
    connector = Neo4jConnector(neo4j_uri, neo4j_user, neo4j_password)

    for i in range(len(corpus)):
        connector.create_corpus_node(i, corpus[i])
        for j in range(i + 1, len(corpus)):
            correlation = compare_corpora(corpus[i], corpus[j])
            connector.create_correlation_relationship(i, j, correlation)

    connector.close()

