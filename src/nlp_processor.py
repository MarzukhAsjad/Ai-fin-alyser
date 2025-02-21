"""
nlp_processor.py
This module provides functionality for summarizing text using Natural Language Toolkit (nltk).
It includes functions for tokenizing text, removing stop words, calculating word frequencies,
and generating a summary based on sentence scores.
Functions:
    make_summary(text, ratio=0.1, max_sentences=10): Generates a summary of the given text by selecting sentences based on word frequencies.
TODO:
    - Replace nltk with a Large Language Model (LLM) for more advanced text processing and summarization.
    - Ensure the new implementation maintains or improves the performance and accuracy of the current summarization process.
    - Update the cache management to handle any new dependencies introduced by the LLM.
"""

import random
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.probability import FreqDist

from corpus_similarity import Similarity

import os

# Define cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".nltk_cache")

# Initialize the corpus similarity module
cs = Similarity(language="eng")


# Ensure necessary NLTK resources are downloaded and stored in cache
nltk.data.path.append(CACHE_DIR)
nltk.download('punkt', download_dir=CACHE_DIR)
nltk.download('stopwords', download_dir=CACHE_DIR)

def make_summary(text, ratio=0.1, max_sentences=10):
    sentences = sent_tokenize(text)
    num_sentences = max(1, int(len(sentences) * ratio))

    # Ensure the number of sentences does not exceed the maximum
    while num_sentences > max_sentences and ratio > 0:
        ratio -= 0.01
        num_sentences = max(1, int(len(sentences) * ratio))

    # Text into words
    words = word_tokenize(text.lower())

    # Removing stop words
    stop_words = set(stopwords.words("english"))
    filtered_words = [word for word in words if word.casefold() not in stop_words]

    # Calculate word frequencies
    fdist = FreqDist(filtered_words)

    # Assign scores to sentences based on word frequencies
    sentence_scores = [sum(fdist[word] for word in word_tokenize(sentence.lower()) if word in fdist)
                       for sentence in sentences]

    # Create a list of tuples containing sentence index and score
    sentence_scores = list(enumerate(sentence_scores))

    # Sort sentences by scores in descending order
    sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)

    # Select the top `num_sentences` sentences for the summary
    summary_sentences = sorted(sorted_sentences[:num_sentences], key=lambda x: x[0])

    # Create the summary
    summary = ' '.join([sentences[i].replace('\n', ' ').replace('\n\n', ' ') for i, _ in summary_sentences])

    return summary

# Add a function to compare two corpora and return the correlation value
def compare_corpora(corpus1, corpus2) -> float:
    result = cs.calculate(corpus1, corpus2)
    print(f"Correlation between corpus1 and corpus2: {result}")
    return result