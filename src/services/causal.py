import pandas as pd
import json
from utils.nlp_processor import compare_corpora
from utils.neo4j_connector import Neo4jConnector

corpus = None
titles = None

# Read the CSV file and extract the titles and content
def read_csv_extract_corpora(file_path: str):
    global corpus, titles
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Drop rows with NaN values or blank cells
    df.dropna(subset=['Title', 'Content'], inplace=True)
    
    # Extract the titles and content
    titles = df['Title'].tolist()
    corpus = df['Content'].tolist()

# Add global variables for progress tracking
progress_data = {
    "total_pairs": 0,
    "processed_pairs": 0,
    "current_status": "Not started"
}

# Store correlation scores between all pairs of corpora in the Neo4j database
def store_correlation_scores():
    global progress_data
    connector = Neo4jConnector()

    if corpus is None or titles is None:
        raise ValueError("Corpus or titles not initialized. Please call read_csv_extract_corpora() first.")
    
    try:
        # First loop: Create all corpus nodes
        for i in range(len(corpus)):
            connector.create_corpus_node(i, titles[i], corpus[i])
        
        # Calculate total number of pairs
        n = len(corpus)
        progress_data["total_pairs"] = (n * (n - 1)) // 2
        progress_data["processed_pairs"] = 0
        progress_data["current_status"] = "Processing"
        
        # Second loop: Compute and store correlations as relationships between nodes
        for i in range(len(corpus)):
            for j in range(i + 1, len(corpus)):
                correlation = compare_corpora(corpus[i], corpus[j])
                if correlation is None:
                    print(f"WARNING: Correlation is None for corpus {i} and {j}")
                connector.create_correlation_relationship(i, j, correlation)
                
                # Update progress
                progress_data["processed_pairs"] += 1
                
        progress_data["current_status"] = "Completed"
        
    except Exception as e:
        progress_data["current_status"] = f"Error: {str(e)}"
        raise
    finally:
        connector.close()

# New generator function to stream progress updates
def store_correlation_scores_stream():
    global progress_data
    connector = Neo4jConnector()
    if corpus is None or titles is None:
        raise ValueError("Corpus or titles not initialized. Please call read_csv_extract_corpora() first.")
    try:
        # First loop: Create all corpus nodes
        for i in range(len(corpus)):
            connector.create_corpus_node(i, titles[i], corpus[i])
        
        # Calculate total number of pairs
        n = len(corpus)
        progress_data["total_pairs"] = (n * (n - 1)) // 2
        progress_data["processed_pairs"] = 0
        progress_data["current_status"] = "Processing"
        yield json.dumps(progress_data) + "\n"
        
        # Second loop: Compute and store correlations as relationships between nodes
        for i in range(len(corpus)):
            for j in range(i + 1, len(corpus)):
                correlation = compare_corpora(corpus[i], corpus[j])
                if correlation is None:
                    print(f"WARNING: Correlation is None for corpus {i} and {j}")
                connector.create_correlation_relationship(i, j, correlation)
                
                # Update progress after each pair processed
                progress_data["processed_pairs"] += 1
                yield json.dumps(progress_data) + "\n"
        
        progress_data["current_status"] = "Completed"
        yield json.dumps(progress_data) + "\n"
    except Exception as e:
        progress_data["current_status"] = f"Error: {str(e)}"
        yield json.dumps(progress_data) + "\n"
        raise
    finally:
        connector.close()

def get_correlation_progress():
    """Get the current progress of correlation calculation"""
    return progress_data

# Wrapper function to query by title
def query_corpus_by_title(title: str):
    connector = Neo4jConnector()
    result = connector.query_by_title(title)
    connector.close()
    return result

# Wrapper function to query all correlations
def query_all_correlations():
    connector = Neo4jConnector()
    result = connector.query_all_correlations()
    connector.close()
    return result

# Wrapper function to query the pairwise highest correlations per corpus
def query_pairwise_causal():
    connector = Neo4jConnector()
    result = connector.query_pairwise_causal()
    connector.close()
    return result

# Wrapper function to query the top N highest correlation relationships
def query_highest_correlation(n: int = 1):
    connector = Neo4jConnector()
    result = connector.query_highest_correlation(n)
    connector.close()
    return result

# Wrapper function to query all corpora (ids, titles, and texts)
def query_all_corpora():
    from utils.neo4j_connector import Neo4jConnector
    connector = Neo4jConnector()
    result = connector.query_all_corpora()
    connector.close()
    return result

# Wrapper function to clear the correlations database
def clear_correlation_database():
    connector = Neo4jConnector()
    connector.clear_database()
    connector.close()
    return "Database cleared."

# Wrapper function to test the Neo4j database connection
def test_db_connection():
    from utils.neo4j_connector import Neo4jConnector  # local import if needed
    connector = Neo4jConnector()
    success = connector.test_connection()
    connector.close()
    return success

