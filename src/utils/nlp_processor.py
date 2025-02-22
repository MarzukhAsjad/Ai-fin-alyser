"""
nlp_processor.py
This module provides functionality for summarizing text using Natural Language Toolkit (nltk).
It includes functions for tokenizing text, removing stop words, calculating word frequencies,
and generating a summary based on sentence scores.
Functions:
    make_summary(text, ratio=0.1, max_sentences=10): Generates a summary of the given text by selecting sentences based on word frequencies.
    compare_corpora(corpus1, corpus2) -> float: Compares two corpora and returns the correlation value.
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
import tempfile
import logging

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
    # Ensure both corpus inputs are strings
    if not isinstance(corpus1, str):
        corpus1 = str(corpus1)
    if not isinstance(corpus2, str):
        corpus2 = str(corpus2)

    logging.info(f"Comparing corpora: {corpus1[:100]}... and {corpus2[:100]}...")
    logging.info(f"Type of corpus1: {type(corpus1)}, Type of corpus2: {type(corpus2)}")

    # Write the corpora to temporary files to ensure compatibility with the corpus similarity module
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp1, tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp2:
        temp1.write(corpus1.encode('utf-8'))
        temp2.write(corpus2.encode('utf-8'))
        temp1_path = temp1.name
        temp2_path = temp2.name

    result = cs.calculate(temp1_path, temp2_path)

    # Clean up temporary files
    os.remove(temp1_path)
    os.remove(temp2_path)

    # Replace NaN with None (or a default value) so JSON can serialize it
    import math
    if result is None or (isinstance(result, float) and math.isnan(result)):
        result = None

    return result