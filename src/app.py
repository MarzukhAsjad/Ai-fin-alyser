from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from .extractor import process_csv_sync, progress, print_data_to_file
import threading

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Function to process CSV in a separate thread
def process_csv_in_thread(contents: bytes):
    process_csv_sync(contents)

# Endpoint to upload CSV files
@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        # Check if the uploaded file is a CSV
        if file.filename.endswith('.csv'):
            contents = await file.read()
            
            # Start a new thread to process the CSV
            thread = threading.Thread(target=process_csv_in_thread, args=(contents,))
            thread.start()
    
            return {"message": "CSV uploaded and processing started"}
        else:
            return {"error": "File is not a CSV"}
    except Exception as e:
        return {"error": str(e)}

# Endpoint to get the progress of the CSV processing
@app.get("/progress/")
def get_progress():
    return progress

# Endpoint to print the DataFrame to a .txt file
@app.get("/print-data/")
def print_data():
    result = print_data_to_file()
    return {"message": result}
