from .nlp_processor import compare_corpora
from .neo4j_connector import Neo4jConnector
import pandas as pd

corpus = None
titles = None

# Read the CSV file and extract the titles and summaries
def read_csv_extract_corpora(file_path: str):
    global corpus, titles
    # Read the CSV file and extract the titles and summaries
    df = pd.read_csv(file_path)
    titles = df['Title'].tolist()
    corpus = df['Summary'].tolist()

# Store correlation scores between all pairs of corpora in the Neo4j database
def store_correlation_scores():
    connector = Neo4jConnector()

    if corpus is None or titles is None:
        raise ValueError("Corpus or titles not initialized. Please call read_csv_extract_corpora() first.")
    
    for i in range(len(corpus)):
        connector.create_corpus_node(i, titles[i], corpus[i])
        for j in range(i + 1, len(corpus)):
            correlation = compare_corpora(corpus[i], corpus[j])
            connector.create_correlation_relationship(i, j, correlation)

    connector.close()

