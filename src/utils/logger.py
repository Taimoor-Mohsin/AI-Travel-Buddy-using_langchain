import json


def pretty_print(label: str, data):
    """Prints the data in a JSON- like pretty format"""
    print(f'"{label}":', json.dumps(data, indent=2, ensure_ascii=False))
