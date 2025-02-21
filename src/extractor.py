import pandas as pd
from io import StringIO

def process_csv(contents: bytes) -> str:
    df = pd.read_csv(StringIO(contents.decode('utf-8')))
    
    # Visualize the data in a table
    table = df.to_string()
    
    # Export the data to a .txt file
    with open("exported_data.txt", "w") as txt_file:
        txt_file.write(table)
    
    return table
