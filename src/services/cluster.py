import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt
from src.services.causal import query_all_correlations
import math

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

# Visualize results with a dendrogram
def visualize_dendrogram(Z, output_path="dendrogram.png"):
    plt.figure(figsize=(10, 7))
    dendrogram(Z)
    plt.title("Hierarchical Clustering Dendrogram")
    plt.xlabel("Document Index")
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

# Main function to run all steps
def run_hierarchical_clustering():
    # Query data
    json_data = sanitize_correlation(query_all_correlations())

    # Convert correlations to distances
    distance_matrix = convert_to_distance_matrix(json_data)

    # Perform hierarchical clustering
    Z = perform_hierarchical_clustering(distance_matrix)

    # Visualize dendrogram
    visualize_dendrogram(Z)

    # Extract clusters (adjust threshold or number of clusters as needed)
    threshold = 1.0   # Example threshold for cutting the dendrogram
    labels = extract_clusters(Z, threshold=threshold)
    
    print("Cluster Labels:", labels)

    return {"Cluster Labels": labels}

