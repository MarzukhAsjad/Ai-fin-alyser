from fastapi import FastAPI, UploadFile, File
from .extractor import process_csv

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# This endpoint will be used to upload CSV files
@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        # Check if the uploaded file is a CSV
        if file.filename.endswith('.csv'):
            contents = await file.read()
            table = process_csv(contents)
    
            return {"message": "CSV uploaded and processed successfully", "table": table}
        else:
            return {"error": "File is not a CSV"}
    except Exception as e:
        return {"error": str(e)}
    