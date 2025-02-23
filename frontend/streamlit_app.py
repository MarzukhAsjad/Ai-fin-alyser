import streamlit as st
import requests
import pandas as pd
import json
import threading
from queue import Queue
from contextlib import contextmanager
from dotenv import load_dotenv
import os
from io import BytesIO
from PIL import Image
import logging
import networkx as nx
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

def process_upload_stream(response):
    """Process streaming response and yield progress updates"""
    progress_bar = None
    status_container = st.empty()
    
    try:
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    
                    # Initialize progress bar when we get the first response
                    if progress_bar is None and 'total' in data:
                        progress_bar = st.progress(0)
                    
                    # Update progress
                    if 'processed' in data and 'total' in data:
                        progress = data['processed'] / data['total']
                        if progress_bar is not None:
                            progress_bar.progress(progress)
                    
                    # Show detailed status updates
                    status_text = [
                        f"Status: {data['status']}",
                        f"Progress: {data.get('processed', 0)} of {data.get('total', '?')} articles"
                    ]
                    
                    if 'errors' in data:        
                        status_text.append(f"Errors in processing articles: {data['errors']}")
                    if 'message' in data:
                        status_text.append(f"Message from API: {data['message']}")
                    
                    status_container.text('\n'.join(status_text))
                    
                    # If complete, return final message
                    if data['status'] == 'complete':
                        return data
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON: {e}")
                    
    except Exception as e:
        logger.error(f"Error processing stream: {e}")
        raise

def main():
    st.title("AI-fin-alyser")
    st.sidebar.title("Navigation")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Choose a function",
        ["Home", "Upload Data", "View Data", "Correlations", "Clustering", "Database Operations"]
    )

    if page == "Home":
        show_home()
    elif page == "Upload Data":
        show_upload_page()
    elif page == "View Data":
        show_view_data()
    elif page == "Correlations":
        show_correlations()
    elif page == "Clustering":
        show_clustering()
    elif page == "Database Operations":
        show_database_operations()

def show_home():
    st.header("Welcome to AI driven financial analysis")
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
        
        with st.spinner("Initializing upload..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/upload/",
                    files=files,
                    stream=True  # Enable streaming response
                )
                
                if response.status_code == 200:
                    final_result = process_upload_stream(response)
                    if final_result and final_result['status'] == 'complete':
                        st.success(final_result['message'])
                else:
                    st.error(f"Upload failed with status code: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error during upload: {e}")

def show_view_data():
    st.header("View Data")
    
    if st.button("Show All Data"):
        with st.spinner("Loading data..."):
            try:
                response = requests.get(f"{API_BASE_URL}/view-data/")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'text/csv' in content_type:
                        # Create a download button for the CSV
                        st.download_button(
                            label="📥 Download CSV",
                            data=response.content,
                            file_name="extracted_data.csv",
                            mime="text/csv"
                        )
                        st.success("Data ready for download!")
                    else:
                        # Handle JSON response (likely an error message)
                        result = response.json()
                        st.write(result)
                else:
                    st.error(f"Failed to load data. Status code: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")

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
    
    # Updated Calculate Correlation button using streaming response
    if st.button("Calculate Correlation"):
        progress_text = st.empty()
        progress_bar = st.progress(0)
        with st.spinner("Calculating correlations..."):
            try:
                response = requests.get(f"{API_BASE_URL}/calculate-correlation/", stream=True)
                for line in response.iter_lines():
                    if line:
                        try:
                            update = json.loads(line.decode("utf-8"))
                            total = update.get("total_pairs", 1)
                            processed = update.get("processed_pairs", 0)
                            status = update.get("current_status", "")
                            progress = processed / total if total else 1
                            
                            progress_bar.progress(progress)
                            progress_text.text(f"Status: {status} — {processed} of {total} pairs processed")
                            
                            if status == "Completed":
                                st.success("Correlation calculation completed!")
                        except Exception as e:
                            st.error(f"Error parsing update: {e}")
            except Exception as e:
                st.error(f"Error during correlation calculation: {e}")
    
    if st.button("Show Pairwise Causal Relations"):
        result = async_api_call(
            requests.get,
            f"{API_BASE_URL}/query-pairwise-causal/",
            loading_text="Loading causal relations..."
        )
        if result and result.get('result'):
            st.subheader("Correlation Network Visualization")
            image_buf = create_correlation_network(result['result'])
            st.image(image_buf, caption="Correlation Network", use_container_width=True)
    
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
    
    # Show confirmation checkbox and button side by side
    col1, col2 = st.columns([3, 1])
    confirm = col1.checkbox("I understand this will clear all data permanently")
    
    if col2.button("Clear Database", disabled=not confirm):
        try:
            response = requests.delete(f"{API_BASE_URL}/clear-database/")
            if response.status_code == 200:
                st.success("Database cleared successfully!")
            else:
                st.error(f"Failed to clear database: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def show_clustering():
    st.header("Hierarchical Clustering Analysis")
    
    # Initialize session state
    if 'clustering_completed' not in st.session_state:
        st.session_state.clustering_completed = False
    
    # Add tabs for different clustering methods
    tab1, tab2 = st.tabs(["Hierarchical Clustering", "LDA Clustering"])
    
    with tab1:
        col1, col2 = st.columns(2)
        # Hierarchical clustering controls
        if col1.button("Run Hierarchical Clustering"):
            result = async_api_call(
                requests.get,
                f"{API_BASE_URL}/run-hierarchical-clustering/",
                loading_text="Running hierarchical clustering..."
            )
            if result and result.get("message") == "Hierarchical clustering completed.":
                st.success("Clustering completed successfully!")
                st.session_state.clustering_completed = True
            else:
                st.error("Clustering failed")
                st.session_state.clustering_completed = False
        
        if col2.button("View Hierarchical Results", disabled=not st.session_state.clustering_completed):
            with st.spinner("Loading clustering visualization..."):
                response = requests.get(f"{API_BASE_URL}/download-hierarchical-clustering-image/")
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    st.image(image, caption="Hierarchical Clustering Results", use_container_width=True)
                else:
                    st.error("Failed to load clustering visualization")
    
    with tab2:
        # LDA clustering controls
        n_topics = st.number_input("Number of Topics", min_value=2, max_value=20, value=5)
        col3, col4 = st.columns(2)
        
        if col3.button("Run LDA Clustering"):
            result = async_api_call(
                requests.get,
                f"{API_BASE_URL}/run-lda-clustering/",
                params={"n_topics": n_topics},
                loading_text="Running LDA clustering..."
            )
            if result and "message" in result:
                st.success(result["message"])
                st.session_state.lda_completed = True
            else:
                st.error("LDA clustering failed")
                st.session_state.lda_completed = False
        
        if col4.button("View LDA Results"):
            with st.spinner("Loading LDA visualization..."):
                response = requests.get(f"{API_BASE_URL}/download-lda-clustering-image/")
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    st.image(image, caption="LDA Clustering Results", use_container_width=True)
                else:
                    st.error("Failed to load LDA visualization")

def create_correlation_network(data):
    # Create a new graph
    G = nx.Graph()
    
    # Add edges with weights
    for item in data:
        source = item['corpusTitle'].replace(' - Wikipedia', '')
        target = item['highestCorrelationCorpus'].replace(' - Wikipedia', '')
        weight = item['highestCorrelation']
        
        # Add edge with weight
        G.add_edge(source, target, weight=weight)
    
    # Create the plot
    plt.figure(figsize=(15, 10))
    
    # Calculate layout (you can experiment with different layouts)
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Draw the network
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=2000, alpha=0.7)
    
    # Draw edges with varying thickness based on correlation
    edges = G.edges()
    weights = [G[u][v]['weight'] * 2 for u, v in edges]  # Scale up weights for visibility
    nx.draw_networkx_edges(G, pos, width=weights, alpha=0.5)
    
    # Add labels
    labels = {node: node for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
    
    plt.title("Correlation Network", pad=20)
    plt.axis('off')
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    plt.close()
    buf.seek(0)
    return buf

if __name__ == "__main__":
    main()
