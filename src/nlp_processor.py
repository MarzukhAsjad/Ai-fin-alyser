"""
This module provides functionality for language processing using NLP techniques.
Functions:
    make_summary(content: str) -> str:
        Abstract method to generate a summary of the given content.
"""

from gensim import summarizer as summarize

def make_summary(content: str) -> str:
    """
    Generate a summary of the given content using Gensim.
    Args:
        content (str): The content to summarize.
    Returns:
        str: The summary of the content.
    """
    try:
        summary = summarize(content)
        return summary
    except ValueError as e:
        return str(e)

