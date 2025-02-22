import streamlit as st
import requests
import pandas as pd
import json
import threading
from queue import Queue
from contextlib import contextmanager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Constants
API_BASE_URL = os.getenv("API_BASE_URL")

def make_async_request(queue, request_func, *args, **kwargs):
    try:
        response = request_func(*args, **kwargs)
        
        # Handle streaming response
        if response.headers.get('content-type') == 'application/x-ndjson':
            # Process streaming JSON
            results = []
            for line in response.iter_lines():
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            queue.put(("success", results))
        else:
            # Handle regular JSON response
            try:
                queue.put(("success", response.json()))
            except requests.exceptions.JSONDecodeError:
                # If JSON parsing fails, return raw text
                queue.put(("success", {"message": response.text}))
    except Exception as e:
        queue.put(("error", str(e)))

@contextmanager
def loading_spinner(text="Processing..."):
    with st.spinner(text):
        yield

def async_api_call(request_func, *args, loading_text="Processing...", **kwargs):
    queue = Queue()
    thread = threading.Thread(
        target=make_async_request,
        args=(queue, request_func, *args),
        kwargs=kwargs,
        daemon=True
    )
    
    with loading_spinner(loading_text):
        thread.start()
        thread.join()
        status, result = queue.get()
        
        if status == "error":
            st.error(f"Error: {result}")
            return None
        return result

def main():
    st.title("Financial Data Analyzer")
    st.sidebar.title("Navigation")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Choose a function",
        ["Home", "Upload Data", "View Data", "Correlations", "Database Operations"]
    )

    if page == "Home":
        show_home()
    elif page == "Upload Data":
        show_upload_page()
    elif page == "View Data":
        show_view_data()
    elif page == "Correlations":
        show_correlations()
    elif page == "Database Operations":
        show_database_operations()

def show_home():
    st.header("Welcome to Financial Data Analyzer")
    if st.button("Test Connection"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/test-connection/",
            loading_text="Testing connection..."
        )
        if result:
            st.write(result)

def show_upload_page():
    st.header("Upload CSV Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        files = {"file": uploaded_file}
        result = async_api_call(
            requests.post,
            f"{API_BASE_URL}/upload/",
            files=files,
            loading_text="Uploading file..."
        )
        if result:
            st.write(result)

def show_view_data():
    st.header("View Data")
    
    if st.button("Show All Data"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/print-data/",
            loading_text="Loading data..."
        )
        if result:
            st.write(result)
    
    st.subheader("Query by Title")
    title = st.text_input("Enter title to search")
    if title and st.button("Search"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/query-by-title/",
            params={"title": title},
            loading_text="Searching..."
        )
        if result:
            st.write(result)

def show_correlations():
    st.header("Correlation Analysis")
    
    if st.button("Calculate Correlation"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/calculate-correlation/",
            loading_text="Calculating correlations..."
        )
        if result:
            st.write(result)
    
    if st.button("Show All Correlations"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/query-all-correlations/",
            loading_text="Loading correlations..."
        )
        if result:
            st.write(result)
    
    if st.button("Show Pairwise Causal Relations"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/query-pairwise-causal/",
            loading_text="Loading causal relations..."
        )
        if result:
            st.write(result)
    
    st.subheader("Highest Correlations")
    limit = st.number_input("Number of top correlations", min_value=1, value=1)
    if st.button("Get Highest Correlations"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/query-highest-correlation/",
            params={"limit": limit},
            loading_text="Finding highest correlations..."
        )
        if result:
            st.write(result)

def show_database_operations():
    st.header("Database Operations")
    
    if st.button("Clear Database"):
        if st.checkbox("Are you sure? This action cannot be undone!"):
            result = async_api_call(
                requests.delete,
                f"{API_BASE_URL}/clear-database/",
                loading_text="Clearing database..."
            )
            if result:
                st.write(result)

if __name__ == "__main__":
    main()
