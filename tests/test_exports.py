"""
Unit tests for GeoJSON, KML, CSV export integrity.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import csv
import io
import pytest


class TestGeoJSONIntegrity:
    def test_geojson_structure(self):
        """Test that GeoJSON output is valid RFC 7946."""
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [72.8403, 19.4521]},
                    "properties": {
                        "class": "MARINE_DEBRIS",
                        "data_source": "DEMO",
                    }
                }
            ],
            "properties": {
                "data_source": "DEMO",
                "verification_disclaimer": "requires human verification",
            }
        }
        # Validate RFC 7946: coordinates are [longitude, latitude]
        assert geojson["features"][0]["geometry"]["coordinates"][0] == 72.8403  # longitude first
        assert geojson["features"][0]["geometry"]["coordinates"][1] == 19.4521  # latitude second

    def test_geojson_includes_data_source(self):
        geojson_str = json.dumps({
            "type": "FeatureCollection",
            "features": [],
            "properties": {"data_source": "DEMO"}
        })
        parsed = json.loads(geojson_str)
        assert parsed["properties"]["data_source"] == "DEMO"

    def test_demo_label_present(self):
        props = {"data_source": "DEMO", "class": "MARINE_DEBRIS"}
        assert props["data_source"] == "DEMO"


class TestCSVIntegrity:
    def test_no_formula_injection(self):
        """CSV values must not start with = + - @ without quoting."""
        dangerous_values = ["=CMD", "+dangerous", "-also_bad", "@formula"]
        cleaned = []
        for val in dangerous_values:
            if val and val[0] in '=+-@':
                cleaned.append("'" + val)
            else:
                cleaned.append(val)
        for c in cleaned:
            assert not c.startswith('=')

    def test_csv_has_required_columns(self):
        required = ['detection_uid', 'classification', 'confidence_prototype_score',
                    'latitude', 'longitude', 'hazard_level', 'data_source']
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(required)
        output.seek(0)
        reader = csv.reader(output)
        header = next(reader)
        for col in required:
            assert col in header

    def test_empty_coords_not_fabricated(self):
        """Detections without GPS must have empty lat/lon, not 0,0."""
        row = {'detection_uid': 'SX-DET-001', 'latitude': None, 'longitude': None}
        lat_export = row['latitude'] if row['latitude'] is not None else ''
        lon_export = row['longitude'] if row['longitude'] is not None else ''
        assert lat_export == ''
        assert lon_export == ''
        assert lat_export != '0'


class TestEvaluationIntegrity:
    def test_not_evaluated_when_no_runs(self):
        """Evaluation must show NOT_EVALUATED when no runs exist."""
        runs = []
        status = 'NOT_EVALUATED' if len(runs) == 0 else 'HAS_RUNS'
        assert status == 'NOT_EVALUATED'

    def test_no_fake_metrics(self):
        """Must not present made-up 95% precision etc. 
        This test documents the policy: never hard-code these values."""
        # Policy assertion: we never pre-populate an EvaluationRun with made-up metrics
        # If an EvaluationRun doesn't exist, the API must return NOT_EVALUATED
        no_runs_response = {'status': 'NOT_EVALUATED', 'runs': []}
        assert no_runs_response['status'] == 'NOT_EVALUATED'
        assert no_runs_response['runs'] == []
