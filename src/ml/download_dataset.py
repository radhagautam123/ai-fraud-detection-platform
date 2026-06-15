import os
import sys
import urllib.request
import zipfile
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings

def download_and_extract():
    url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/creditcard.csv.zip"
    dest_dir = settings.DATA_RAW_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = dest_dir / "creditcard.csv.zip"
    csv_path = settings.KAGGLE_DATASET_PATH
    
    print(f"Downloading dataset from {url}...")
    try:
        # Download file
        urllib.request.urlretrieve(url, zip_path)
        print("Download complete. Extracting file...")
        
        # Extract file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
            
        print(f"Extraction complete. Processing dataset to add headers...")
        
        # Load headerless CSV and write headers
        if csv_path.exists():
            # Read without headers
            df = pd.read_csv(csv_path, header=None)
            
            # Assign Kaggle dataset headers
            df.columns = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
            
            # Save back with headers
            df.to_csv(csv_path, index=False)
            print(f"Headers added successfully. Saved to {csv_path}")
            
            # Clean up zip file
            if zip_path.exists():
                zip_path.unlink()
                print("Cleaned up temporary zip file.")
                
            # Final validation
            print(f"Verified dataset shape: {df.shape}")
            print(f"Verified class counts: {df['Class'].value_counts().to_dict()}")
        else:
            print("Error: creditcard.csv was not found after extraction.")
            sys.exit(1)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_and_extract()
