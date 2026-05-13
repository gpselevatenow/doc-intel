import json
import asyncio
import sys
sys.path.append('.')
from main import extract_police
from fastapi import UploadFile
from unittest.mock import MagicMock
import tempfile

def test_extract():
    # Create a mock upload file
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "sample_07_rain_injury.pdf"
    
    # We need to provide a real file object
    with open("../sample_07_rain_injury.pdf", "rb") as f:
        mock_file.file = f
        
        result = asyncio.run(extract_police(mock_file))
        print("RESULT BBOX MAP:")
        print(json.dumps(result.get("bbox_map", {}), indent=2))
        print("RESULT DYNAMIC FIELDS:")
        print(json.dumps(result.get("dynamic_fields", {}), indent=2))
        
if __name__ == "__main__":
    test_extract()
