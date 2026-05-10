import base64
import zlib
import urllib.request
import sys

mermaid_code = """
graph TD
    classDef frontend fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
    classDef backend fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#fff
    classDef logic fill:#334155,stroke:#fef08a,stroke-width:2px,color:#fff
    classDef datastore fill:#475569,stroke:#fbbf24,stroke-width:2px,color:#fff
    classDef external fill:#000000,stroke:#ef4444,stroke-width:2px,color:#fff

    subgraph Frontend ["Frontend (React + Vite)"]
        UI["Glassmorphic UI Engine"]
        Results["Extraction Results Component"]
        ReviewFlags["Low-Confidence Alert UI"]
        Viewer["PDF Viewer Component"]
        BboxPlugin["Custom BboxPlugin<br>(Absolute CSS Overlay)"]
        Editable["Inline Editable UI (Human-in-the-Loop)"]
    end

    subgraph Backend ["Backend (FastAPI)"]
        API["FastAPI Server (main.py)"]
        Docling["Docling Parser<br>(Generates Canonical Doc)"]
        
        subgraph Engine ["Declarative Extraction Engine"]
            Templates["JSON Templates"]
            Orchestrator["Orchestrator Core"]
            Extractors["Spatial & Regex Extractors"]
            Validation["Scoring & Validation Pipeline"]
        end
        
        DB[("feedback.db<br>(SQLite)")]
    end

    subgraph FutureIntegrations ["Future Release"]
        ClaimCenter["Guidewire ClaimCenter APIs"]
    end

    User((Adjuster)) --> API
    API --> Docling
    Docling --> Orchestrator
    Templates --> Orchestrator
    DB --> Orchestrator
    Orchestrator --> Extractors
    Extractors --> Validation
    Validation --> Orchestrator
    Orchestrator --> Results
    Results --> ReviewFlags
    Results --> Editable
    Results --> UI
    UI --> BboxPlugin
    BboxPlugin --> Viewer
    User --> Editable
    Editable --> DB
    User --> ClaimCenter

    class UI,Results,ReviewFlags,Viewer,BboxPlugin,Editable frontend
    class API,Docling backend
    class Orchestrator,Templates,Extractors,Validation logic
    class DB datastore
    class ClaimCenter external
"""

# Compress using zlib
compressed = zlib.compress(mermaid_code.encode('utf-8'))
# Encode base64 url-safe
encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')

url = f"https://kroki.io/mermaid/png/{encoded}"
print("Fetching from:", url)

try:
    urllib.request.urlretrieve(url, "diagram.png")
    print("Successfully downloaded diagram.png")
except Exception as e:
    print("Error:", e)
    sys.exit(1)
