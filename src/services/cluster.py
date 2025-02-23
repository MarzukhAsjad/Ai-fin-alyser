import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib
matplotlib.use('Agg')  # Set backend to non-interactive Agg
import matplotlib.pyplot as plt
from services.causal import query_all_correlations
import math
import logging
import pandas as pd  # NEW: to read printed_data.csv for titles

logger = logging.getLogger(__name__)

# Convert correlations into distances
def convert_to_distance_matrix(json_data):
    result = json_data["result"]
    n_docs = max(max(item['id1'], item['id2']) for item in result) + 1

    # Initialize the similarity matrix
    similarity_matrix = np.zeros((n_docs, n_docs))

    # Fill the similarity matrix
    for item in result:
        id1 = item["id1"]
        id2 = item["id2"]
        correlation = item["correlation"]
        similarity_matrix[id1][id2] = correlation
        similarity_matrix[id2][id1] = correlation

    # Fill diagonal with ones (self-similarity)
    np.fill_diagonal(similarity_matrix, 1)

    # Convert similarity to distance
    distance_matrix = np.sqrt(2 * (1 - similarity_matrix))
    return distance_matrix

# Perform hierarchical clustering using linkage
def perform_hierarchical_clustering(distance_matrix):
    # Use only the upper triangular part of the distance matrix for linkage
    Z = linkage(distance_matrix[np.triu_indices_from(distance_matrix, k=1)], method="ward")
    return Z

# NEW: Update visualize_dendrogram to accept id_title mapping
def visualize_dendrogram(Z, id_title, output_path="hierarchical_clustering.png"):
    plt.figure(figsize=(10, 7))
    # Use leaf_label_func to replace id with title
    dendrogram(Z, leaf_label_func=lambda x: id_title.get(int(x), str(x)))
    plt.title("Hierarchical Clustering Dendrogram")
    plt.xlabel("Document")
    plt.ylabel("Distance")
    plt.savefig(output_path)
    plt.close()

# Extract flat clusters
def extract_clusters(Z, threshold=None, n_clusters=None):
    if threshold:
        # Cut dendrogram at a specific distance threshold
        labels = fcluster(Z, t=threshold, criterion="distance")
    elif n_clusters:
        # Specify the number of clusters
        labels = fcluster(Z, t=n_clusters, criterion="maxclust")
    else:
        raise ValueError("Either 'threshold' or 'n_clusters' must be provided.")
    
    return labels

# Sanitize correlation values
def sanitize_correlation(result):
    # Sanitize correlation values as before
    sanitized = []
    for record in result:
        corr = record.get("correlation")
        if corr is not None and math.isfinite(corr):
            corr = round(corr, 5)
        if corr is None or not math.isfinite(corr):
            record["correlation"] = None
        sanitized.append(record)
    return {"result": sanitized}

# Main function to run clustering with custom leaf labeling
def run_hierarchical_clustering():
    try:
        # Query data
        json_data = sanitize_correlation(query_all_correlations())

        # Convert correlations to distances
        distance_matrix = convert_to_distance_matrix(json_data)

        # Perform hierarchical clustering
        Z = perform_hierarchical_clustering(distance_matrix)

        # NEW: Build id_title mapping from printed_data.csv
        df = pd.read_csv("printed_data.csv")
        id_title = dict(enumerate(df["Title"].tolist()))
        
        # Call updated visualization with custom labels
        visualize_dendrogram(Z, id_title)
        
        logger.info("Hierarchical clustering completed.")
        return {"message": "Hierarchical clustering completed."}
        
    except Exception as e:
        logger.error(f"Error in hierarchical clustering: {e}")
        raise

