from fastapi import FastAPI, UploadFile, File
import pandas as pd
from io import StringIO

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# This endpoint will be used to upload CSV files
@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(StringIO(contents.decode('utf-8')))
    
    # Visualize the data in a table
    table = df.to_string()
    
    # Export the data to a .txt file
    with open("exported_data.txt", "w") as txt_file:
        txt_file.write(table)
    
    return {"message": "CSV uploaded and processed successfully"}