import json
from backend.core.parser import parse_document
from backend.core.template_schema import TemplateSchema, FieldDefinition, FieldStrategy
from backend.core.orchestrator import extract

md, doc = parse_document("sample_07_rain_injury.pdf")

template = TemplateSchema(
    template_id="police_01",
    document_type="police_report",
    fields=[
        FieldDefinition(
            field_id="location",
            field_type="text",
            strategies=[
                FieldStrategy(
                    strategy="nearby_text",
                    config={"anchor_text": "Location", "direction": "right"}
                )
            ]
        ),
        FieldDefinition(
            field_id="weather",
            field_type="text",
            strategies=[
                FieldStrategy(
                    strategy="nearby_text",
                    config={"anchor_text": "Weather", "direction": "right"}
                )
            ]
        )
    ]
)

result = extract(doc, template)
print("EXTRACTED:")
print(json.dumps(result["record"], indent=2))
