GHOST_PREDICTIONS = {
    "tx_cr3": {
        "agency": "Fort Worth Police Department",
        "report_number": "TR-{year}-{seq}",
        "ems_agency": "MedStar Mobile Healthcare",
        "road_surface": "Dry",
        "light_condition": "Daylight",
    },
    "municipal_pd_collision": {
        "road_surface": "Dry",
        "light_condition": "Daylight",
        "property_damage": "None reported",
    },
    "ny_mv104a": {
        "agency": "New York City Police Department",
        "road_surface": "Dry",
    },
    "ia_report": {
        "coverage_b": "N/A",
        "coverage_d": "N/A",
        "payment_summary": "N/A",
    },
}

CONFIDENCE_LABELS = {
    "tx_cr3": {
        "agency": 0.82,
        "ems_agency": 0.71,
        "road_surface": 0.65,
        "light_condition": 0.60,
    },
    "municipal_pd_collision": {
        "road_surface": 0.60,
        "light_condition": 0.58,
        "property_damage": 0.55,
    },
    "ia_report": {
        "coverage_b": 0.88,
        "coverage_d": 0.88,
        "payment_summary": 0.92,
    },
}


def get_ghost_predictions(form_id: str, early_signals: dict) -> list:
    """
    Returns list of ghost prediction events based on form_id
    and early extracted values.
    """
    predictions = []
    base = GHOST_PREDICTIONS.get(form_id, {})
    conf = CONFIDENCE_LABELS.get(form_id, {})

    for field_id, predicted_value in base.items():
        value = predicted_value
        if '{year}' in str(value):
            year = str(early_signals.get('date_time', '2026'))[:4]
            value = value.replace('{year}', year)
        if '{seq}' in str(value):
            value = value.replace('{seq}', 'XXXXX')

        predictions.append({
            "type": "ghost",
            "field_id": field_id,
            "predicted_value": value,
            "confidence": conf.get(field_id, 0.60),
            "basis": f"Based on {form_id} pattern",
        })

    return predictions
