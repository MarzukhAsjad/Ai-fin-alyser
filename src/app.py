from fastapi import FastAPI, UploadFile, File
from .extractor import process_csv, progress
import threading

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

def process_csv_in_thread(contents: bytes):
    process_csv(contents)

# This endpoint will be used to upload CSV files
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

# This endpoint will be used to get the progress of the CSV processing
@app.get("/progress/")
def get_progress():
    return progress
