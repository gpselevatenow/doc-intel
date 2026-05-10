import json
import os
from backend.core.document_model import Document
from backend.core.template_schema import TemplateSchema, FieldDefinition, FieldStrategy
from backend.core.orchestrator import extract
from backend.database import get_custom_fields

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

def run_orchestrator(canonical_doc: Document, doc_id: str, doc_type: str) -> dict:
    """
    Loads a base JSON template for the document type, appends dynamic Custom Fields
    from the database, and executes the orchestrator extraction engine.
    """
    template_path = os.path.join(TEMPLATES_DIR, f"{doc_type}.json")
    
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)
    else:
        # Fallback empty template
        template_data = {
            "template_id": f"fallback_{doc_type}",
            "document_type": doc_type,
            "fields": []
        }

    # Load into Pydantic model
    template = TemplateSchema(**template_data)

    # Fetch custom fields requested by user (Human-in-the-Loop)
    custom_fields = get_custom_fields(doc_id)
    for field_name in custom_fields:
        # Generate a dynamic FieldDefinition using global_regex
        pattern = f"(?i){field_name}[\\s:]*(?P<value>.+?)(?:\\n|$)"
        dynamic_field = FieldDefinition(
            field_id=f"dynamic_{field_name}",
            display_name=field_name,
            field_type="text",
            strategies=[
                FieldStrategy(
                    strategy="global_regex",
                    priority=1,
                    config={
                        "patterns": [pattern],
                        "flags": ["IGNORECASE"]
                    }
                )
            ]
        )
        template.fields.append(dynamic_field)

    # Run the engine
    result = extract(canonical_doc, template)
    
    # Parse audit logs for review flags
    review_flags = {}
    for entry in result.get("audit", []):
        if entry.get("needs_review"):
            review_flags[entry["field_id"]] = True
            
    return {
        "record": result["record"],
        "review_flags": review_flags
    }
