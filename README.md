# Ai-fin-alyser

This tool will analyse CSVs, extract articles from the CSVs, visualize the causal relationship between the content of the articles and then cluster the modules into distinct classes accordingly. The tool's backend is created with FastAPI and the frontend interface is created with Streamlit. The database for storing the relationships is the Neo4j database.

# Outline

- [Download the Repository](#download-the-repository)
- [Installation Instructions](#installation-instructions)
  - [Create a Virtual Environment](#create-a-virtual-environment)
  - [Install the Requirements](#install-the-requirements)
  - [Set Up the Environment Variables](#set-up-the-environment-variables)
  - [Run the Backend Application](#run-the-backend-application)
  - [Run the Frontend Application](#run-the-frontend-application)
  - [Run the Neo4j Database](#run-the-neo4j-database)
- [Docker Installation](#docker-installation)
  - [Build the Docker Image](#build-the-docker-image)
  - [Run the Docker Container](#run-the-docker-container)
- [Usage](#usage)
  - [Upload a CSV File](#upload-a-csv-file)
  - [Get the Output Dataframe](#get-the-output-dataframe)
  - [Calculate Causal Relationship](#calculation-of-causal-relationship)
  - [Query Pairwise Causal Relationship](#query-pairwise-causal-relationship)
  - [Query Highest Causal Relationship](#query-highest-causal-relationship-based-on-the-correlation-score)
  - [Delete the Graph Database](#delete-the-graph-database)
  - [Test Connection to Neo4j Database](#test-connection-to-the-neo4j-database)
  - [Perform Hierarchical Clustering](#perform-hierarchical-clustering)
  - [Download Hierarchical Clustering Results](#download-the-hierarchical-clustering-results)
  - [Perform LDA Clustering](#perform-lda-clustering)
  - [Download LDA Clustering Results](#download-the-lda-clustering-results)
- [Features](#features)
  - [Summarization Tool](#summarisation-tool)
  - [Rate Limiting](#rate-limiting)
  - [Asynchronous Fast Processing](#asynchronous-fast-processing)
  - [Task Queue with asyncio.Queue](#task-queue-with-asyncioqueue)
  - [Causal Relationship Visualization](#causal-relationship-visualization)
  - [Hierarchical Clustering Details](#hierarchical-clustering)
  - [LDA Clustering Details](#lda-clustering)

# Download the repository

Download the repository before you can proceed with how to install.

```bash
git clone https://github.com/MarzukhAsjad/Ai-fin-alyser.git
```

# Installation instructions

You can either set up the three individual elements (backend, frontend and database) separately with the following instructions or you may directly jump to the Docker set up for an easy installation.

## Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## Install the requirements

```bash
pip install -r requirements.txt
```

## Set up the environment variables

Create a .env file in the root of this project

```dotenv
NEO4J_URI=http://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mysecretpassword
API_BASE_URL=http://localhost:8000
NEO4J_AUTH=neo4j/mysecretpassword
```

## Run the backend application

```bash
cd Ai-fin-alyser
uvicorn src.app:app --reload
```

## Run the frontend application
```
cd Ai-fin-alyser/frontend
streamlit run streamlit_app.py
```

## Run the Neo4j database

This is a heavy application and is recommended to be run with Docker

```bash
docker run -d \
  --name neo4j-container \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

The Neo4j browser will be up at http://localhost:7474 whereas the bolt server will be up at bolt://localhost:7687 or http://localhost:7687

# Docker installation

This has been tested on a Linux environment. The following steps will guide you on how to set up the application using Docker.

## Build the Docker image

```bash
cd Ai-fin-alyser
docker compose build
```

## Run the Docker container

```bash
docker compose up
```

The streamlit application should be available in the browser at `http://localhost:8501`.

# Usage

All of the following functions are available to invoke via the Streamlit User Interface. However, one can also separately request to the API. In order for a smooth execution, it is recommended to do the followiing steps sequentially whether via API or Streamlit.

## Format of the CSV file

The CSV file structure is rather simple with two columns, source and URL

![image](https://github.com/user-attachments/assets/01dbc506-d395-40a6-abba-a3c9ffc95a99)

## Upload a CSV file

```bash
curl -X POST "http://localhost:8000/upload" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@/path/to/your/file.csv"
```

This will upload the CSV file and start processing. The endpoint will stream back the processing status in JSON format:

```json
{"status": "processing", "total": 30, "processed": 1, "errors": 0}
{"status": "processing", "total": 30, "processed": 2, "errors": 0}
{"status": "processing", "total": 30, "processed": 3, "errors": 1}
...
{"status": "complete", "message": "Processing complete", "total": 30, "processed": 30, "errors": 2}
```

Possible response formats:
- Processing updates: `{"status": "processing", "total": X, "processed": Y, "errors": Z}`
- Completion message: `{"status": "complete", "message": "Processing complete", "total": X, "processed": Y, "errors": Z}`
- Error messages: `{"status": "error", "message": "error description"}`
- Cancellation message: `{"status": "cancelled", "message": "Processing was cancelled"}`

## Get the output dataframe

This endpoint will return the output CSV to view the dataframe that was created with the title, content and summary of the articles. It also includes a column to indicate whether the article was acccessible.

```bash
curl -X GET "http://localhost:8000/view-data" -H "accept: application/json"
```

## Calculation of causal relationship

This endpoint will calculate the causal relationship between the articles based on the similarity of the words in the articles. The causal relationship is then stored in a Neo4j graph database.

```bash
curl -X POST "http://localhost:8000/calculate-correlation" -H "accept: application/json"
```


## Query pairwise causal relationship

This endpoint will query the Neo4j graph database to visualize the causal relationship for each article and the rest, returning the highest causal relationship for each article.

```bash
curl -X GET "http://localhost:8000/query-pairwise-causal" -H "accept: application/json"
```

The endpoint will return the highest causal relationship for each article in JSON format.

```json
{
    "result": [
        {
            "corpusTitle": "Article 1",
            "highestCorrelationCorpus": "Article 3",
            "highestCorrelation": 0.611137484440765
        },
        {
            "corpusTitle": "Article 2",
            "highestCorrelationCorpus": "Article 9",
            "highestCorrelation": 0.6021493226575421
        }
    ]
}
```

## Query highest causal relationship based on the correlation score

This endpoint allows the user to query the highest correlation from the dataset. The user can specify the number of top correlations to return using the `limit` parameter.

```bash
curl -X GET "http://localhost:8000/query-highest-correlation?limit=5" -H "accept: application/json"
```

The endpoint will return the top correlations in JSON format.

```json
{
    "result": [
        {
            "corpus1": "Article 1",
            "corpus2": "Article 3",
            "correlation": 0.611137484440765
        },
        {
            "corpus1": "Article 2",
            "corpus2": "Article 9",
            "correlation": 0.6021493226575421
        }
    ]
}
```

## Delete the graph database

This endpoint will delete the graph database.

```bash
curl -X DELETE "http://localhost:8000/clear-database" -H "accept: application/json"
```

The endpoint will return a message indicating that the database has been cleared.

```json
{
    "message": "Database cleared"
}
```

## Test connection to the Neo4j database

This endpoint will test the connection to the Neo4j database from the API.

```bash
curl -X GET "http://localhost:8000/test-connection" -H "accept: application/json"
```

The endpoint will return a message indicating that the connection was successful or unsuccessful.

```json
{
    "connection_successful": true
}
```

## Perform hierarchical clustering

This endpoint will cluster the articles into hierarchical groups based on the content of the articles. This uses the correlation score of the articles as similarity measure to cluster the articles.

```bash
curl -X POST "http://localhost:8000/run-hierarchical-clustering" -H "accept: application/json"
```

The endpoint will return a success message indicating that the clustering was successful.

```json
{
    "message": "Hierarchical clustering completed"
}
```

## Download the hierarchical clustering results

This endpoint will download the hierarchical clustering results as a PNG file which displays the tree structure of the clusters.

```bash
curl -X GET "http://localhost:8000/download-hierarchical-clustering-image" -H "accept: application/json"
```

The endpoint will return the PNG file if it exists, or an error message if the file is not found.

```json
{
    "error": "Clustering image not found at /absolute/path/to/hierarchical_clustering.png"
}
```

## Perform lda clustering

This endpoint will cluster the articles into distinct groups based on the content of the articles using Latent Dirichlet Allocation (LDA) clustering.

```bash
curl -X POST "http://localhost:8000/run-lda-clustering" -H "accept: application/json"
```

This endpoint will return the following json on success:

```json
{
    "message": "LDA clustering completed"
}
```

## Download the lda clustering results

This endpoint will download the lda clustering results as a PNG file which displays the clustered structure of the articles.

```bash
curl -X GET "http://localhost:8000/download-lda-clustering-image" -H "accept: application/json"
```

The endpoint will return the PNG file if it exists, or an error message if the file is not found.

```json
{
    "error": "Clustering image not found at /absolute/path/to/lda_clustering.png"
}
```

# Features

## Summarisation tool

The summarization tool leverages the Natural Language Toolkit (nltk) to generate concise summaries of text. The `make_summary` function processes the text by tokenizing it into sentences and words, removing stop words, and calculating word frequencies. Sentences are then scored based on the frequency of their words. The function selects the top sentences according to their scores to form the summary. The length of the summary can be adjusted using the `ratio` parameter, which determines the proportion of sentences to include, and the `max_sentences` parameter, which sets an upper limit on the number of sentences in the summary.

## Rate limiting

The application implements rate limiting using the `slowapi` library to control the number of requests a unique IP address can make to the API endpoints. This helps to prevent abuse and ensures fair usage of the API.

## Asynchronous fast processing

The application uses FastAPI's asynchronous capabilities to process CSV files quickly and efficiently. The `upload` endpoint processes the CSV file asynchronously, allowing the user to continue interacting with the API while the file is being processed. The processing rate is streamed back to the user in real-time, providing feedback on the progress of the operation. By using asynchronous processing, the duration for processing large CSV files is significantly reduced, improving the user experience.

## Task queue with asyncio.Queue

The application uses `asyncio.Queue` to manage tasks efficiently. This queue allows the application to handle multiple tasks concurrently without blocking the main thread. When a CSV file is uploaded, tasks are added to the queue and processed asynchronously. This ensures that the application remains responsive and can handle multiple file uploads simultaneously while retaining the sequential order of processing.

## Causal relationship visualization

Calculate the causal correlation between the content of the articles based on similarity of the words in the articles. This is assuming that articles with similar content are likely to have a causal relationship. Afterwards, the API stores the causal correlation in a graph database, explicitly defining the causal relationship between the articles in a Neo4j graph database. Finally, it allows the user to query the graph database to visualize the causal relationship between the content of the articles. There are some endpoints for dynamic queries to be made to the API to visualize the causal relationship between the articles.

## Hierarchical clustering

Cluster the articles into distinct groups based on the content of the articles. This uses the correlation score of the articles as a similarity measure to cluster the articles. The similarity score is then used to calculate the distance between the articles by the formula $\sqrt{2*(1-similarity)}$

The hierarchical clustering algorithm then clusters the articles into distinct groups based on the distance between the articles. Because there are multiple articles, this is done by grouping all of them in a distance matrix. Afterwards, the algorithm uses the following to calculate the linkage matrix (Z):

```python
Z = linkage(distance_matrix[np.triu_indices_from(distance_matrix, k=1)], method="ward")
```

Using flat clustering and the Z matrix, the algorithm then uses the following to cluster the articles:

```python
labels = fcluster(Z, t=n_clusters, criterion="maxclust")
```

or the following if no number of clusters is specified:

```python
labels = fcluster(Z, t=threshold, criterion="distance")
```

The algorithm then plots the dendrogram of the hierarchical clustering to visualize the distinct groups of articles. The threshold for the clustering can be adjusted using the `threshold` parameter.

## LDA clustering

Cluster the articles into distinct groups based on the content of the articles using Latent Dirichlet Allocation (LDA) clustering. LDA is a generative probabilistic model that allows sets of observations to be explained by unobserved groups that explain why some parts of the data are similar. The LDA clustering algorithm assigns each article to a distinct group based on the content of the articles. The number of clusters can be adjusted using the `n_clusters` parameter. This algorithm uses the raw text from the articles to perform the clustering rather than the correlation score.
