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
        plt.figure(figsize=(10, 6))
        plt.scatter(ids, clusters, c=clusters, cmap='viridis')
        plt.xlabel("Document ID")
        plt.ylabel("Cluster")
        plt.title("LDA Clustering Visualization")
        plt.colorbar(label="Cluster")
        # Annotate each point with its document id
        for doc_id, cluster in zip(ids, clusters):
            plt.text(doc_id, cluster, str(doc_id), fontsize=8, ha='center', va='bottom')
        plt.savefig(output_path)
        plt.close()

    def run(self, corpus, ids):
        clusters, _ = self.fit_transform(corpus)
        self.visualize_clusters(ids, clusters)
        self.logger.info("LDA clustering completed.")
        # Return a mapping from document id to its cluster label
        return dict(zip(ids, clusters))
