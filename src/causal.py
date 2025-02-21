from .nlp_processor import compare_corpora
from .neo4j_connector import Neo4jConnector
import pandas as pd

corpus = None

# Read the CSV file and extract the corpora
def read_csv_extract_corpora(file_path: str) -> list:
    global corpus
    # Read the CSV file and extract the corpus
    df = pd.read_csv(file_path)
    corpus = df['Summary'].tolist()

# Store correlation scores between all pairs of corpora in the Neo4j database
def store_correlation_scores(neo4j_uri: str, neo4j_user: str, neo4j_password: str):
    connector = Neo4jConnector(neo4j_uri, neo4j_user, neo4j_password)

    if corpus is None:
        raise ValueError("Corpus not initialized. Please call read_csv_extract_corpora() first.")
    
    for i in range(len(corpus)):
        connector.create_corpus_node(i, corpus[i])
        for j in range(i + 1, len(corpus)):
            correlation = compare_corpora(corpus[i], corpus[j])
            connector.create_correlation_relationship(i, j, correlation)

    connector.close()

