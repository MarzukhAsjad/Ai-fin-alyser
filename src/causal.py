from .nlp_processor import compare_corpora
from .neo4j_connector import Neo4jConnector

def compare_and_pair(corpus: list, neo4j_uri: str, neo4j_user: str, neo4j_password: str) -> list:
    connector = Neo4jConnector(neo4j_uri, neo4j_user, neo4j_password)
    pairs = []

    for i in range(len(corpus)):
        connector.create_corpus_node(i, corpus[i])
        for j in range(i + 1, len(corpus)):
            connector.create_corpus_node(j, corpus[j])
            correlation = compare_corpora(corpus[i], corpus[j])
            pairs.append(((i, j), correlation))
            connector.create_correlation_relationship(i, j, correlation)

    connector.close()
    return pairs

