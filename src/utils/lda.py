import re
import logging
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

class LDA:
    def __init__(self, n_topics=5, max_iter=10, random_state=42):
        self.n_topics = n_topics
        self.max_iter = max_iter
        self.random_state = random_state
        self.vectorizer = CountVectorizer(stop_words='english')
        self.model = LatentDirichletAllocation(n_components=n_topics,
                                               max_iter=max_iter,
                                               random_state=random_state)
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text):
        # lowercasing and remove non-alphabet characters
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        return text

    def fit_transform(self, corpus):
        # Clean the corpus
        cleaned_corpus = [self.clean_text(doc) for doc in corpus]
        # Convert texts to document-term matrix
        dt_matrix = self.vectorizer.fit_transform(cleaned_corpus)
        # Compute topic distributions using LDA
        topic_distribution = self.model.fit_transform(dt_matrix)
        # Assign each document to the topic with highest probability
        clusters = np.argmax(topic_distribution, axis=1)
        return clusters, topic_distribution

    def visualize_clusters(self, ids, clusters, output_path="lda_clusters.png"):
        # Create a figure with two subplots in 70:30 ratio
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw={'width_ratios': [7, 3]})
        
        # Plot clusters on the left
        scatter = ax1.scatter(ids, clusters, c=clusters, cmap='viridis')
        ax1.set_xlabel("Document ID")
        ax1.set_ylabel("Topic Cluster")
        ax1.set_title("LDA Topic Clustering")
        
        # Get titles from printed_data.csv
        import pandas as pd
        df = pd.read_csv("printed_data.csv")
        id_title = dict(enumerate(df["Title"].tolist()))
        
        # Create legend handles on the right
        handles = [plt.Line2D([0], [0], marker='o', color='w', 
                            markerfacecolor=scatter.cmap(scatter.norm(cluster)), 
                            markersize=5, 
                            label=f"ID {doc_id}: {id_title.get(doc_id, 'Unknown')}") 
                  for doc_id, cluster in zip(ids, clusters) if id_title.get(doc_id) != "No Title"]
        
        # Add legend to right subplot
        ax2.legend(handles=handles, loc='center', bbox_to_anchor=(0.5, 0.5))
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

    def run(self, corpus, ids):
        clusters, _ = self.fit_transform(corpus)
        self.visualize_clusters(ids, clusters)
        self.logger.info("LDA clustering completed.")
        # Return a mapping from document id to its cluster label
        return dict(zip(ids, clusters))
