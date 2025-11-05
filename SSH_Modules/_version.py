
import json

version_json = '''
{"date": "2025-10-12T13:14:49.841192", "dirty": false, "error": null, "full-revisionid": "c92aa3eee8905a3983a80e7105b523b113068438", "version": "1.2.0.post1"}'''  # END VERSION_JSON


def get_versions():
    return json.loads(version_json)

