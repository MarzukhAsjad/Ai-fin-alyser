"""
nlp_processor.py
This module provides functionality for summarizing text using Natural Language Toolkit (nltk).
It includes functions for tokenizing text, removing stop words, calculating word frequencies,
and generating a summary based on sentence scores.
Functions:
    make_summary(text): Generates a summary of the given text by selecting sentences based on word frequencies.
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
import os

# Define cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".nltk_cache")

# Ensure necessary NLTK resources are downloaded and stored in cache
nltk.data.path.append(CACHE_DIR)
nltk.download('punkt', download_dir=CACHE_DIR)
nltk.download('stopwords', download_dir=CACHE_DIR)

def make_summary(text):
    sentences = sent_tokenize(text)
    num_sentences = min(len(sentences), text.count('.') + text.count('!') + text.count('?'))

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

    # Randomly select the top `num_sentences` sentences for the summary
    random_sentences = random.sample(sorted_sentences, min(num_sentences, len(sorted_sentences)))

    # Sort the randomly selected sentences based on their original order in the text
    summary_sentences = sorted(random_sentences, key=lambda x: x[0])

    # Create the summary
    summary = ' '.join([sentences[i] for i, _ in summary_sentences])

    return summary