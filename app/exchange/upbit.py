import requests
import datetime
import ccxt

class Upbit():
    def __init__(self):
        pass
    def get_market(self):
        url = "https://api.upbit.com/v1/market/all"
        querystring = {"isDetails":"false"}
        response = requests.request("GET", url, params=querystring)
        print(response.text)

Upbit.get_market()