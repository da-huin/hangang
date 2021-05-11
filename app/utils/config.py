import json
import os

def get(key):
    with open(os.path.dirname(os.path.dirname(__file__)) + '/config.json') as fp:
        json.loads(fp.read())

