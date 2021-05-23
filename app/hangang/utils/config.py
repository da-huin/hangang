import json
import os

def get(key):
    with open(os.path.dirname(os.path.dirname(__file__)) + '/config.json', 'r') as fp:
        return json.loads(fp.read())[key]

