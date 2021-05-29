import requests
import datetime
import ccxt
import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

class Upbit:
    
    # Candlestick -> backtest
    # Real time price -> real time test / actual transaction

    def __init__(self, order_currency):
        self._order_currency = order_currency

    def get_my_asset(self): # Load status of my asset
        payload = {
            'access_key': 'API_ACCESS_KEY', # Your API access key here
            'nonce': str(uuid.uuid4())
        }
        jwt_token = jwt.encode(payload, 'API_SECRET_KEY') # Your API secret key here
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get('https://api.upbit.com/v1/accounts', headers=headers)

        # print(res.json())

        print("====Loading asset====")
        for i in range(len(res.json())):
            print("Currency: {}".format(res.json()[i].get('currency')))
            print("Balance: {}".format(res.json()[i].get('balance')))
            print("Locked: {}".format(res.json()[i].get('locked')))
            print("Average buy price: {}".format(res.json()[i].get('avg_buy_price')))
            print("Unit currency: {}".format(res.json()[i].get('unit_currency')), "\n")

    # def get_market(self): # Load all of market data except price, etc. Probably we won't need this.
    #     url = "https://api.upbit.com/v1/market/all"
    #     querystring = {"isDetails":"false"}
    #     response = requests.request("GET", url, params=querystring)
    #     print(response.text)
    
    def get_market_data(self, item, minute):
        url = "https://api.upbit.com/v1/candles/minutes/" + str(minute)

        market = "KRW-" + str(item)
        querystring = {"market":market,"count":"200"}
        response = requests.request("GET", url, params=querystring)
        print(response.text)

    def get_ticker_data(self, item):
        url = "https://api.upbit.com/v1/ticker"

        for i in range(len(item)):
            item[i] = "KRW-" + item[i]
        ', '.join(item) # Concatenate strings

        querystring = {"markets":item}
        headers = {"Accept": "application/json"}
        response = requests.request("GET", url, headers=headers, params=querystring)

        print(response.text)

    def get_candle(self, time_type, item, to, minute=0, period=200):
        base_url = 'https://api.upbit.com/v1/candles'
        if time_type == 'minute':
            url = f"{base_url}/minutes/" + str(minute)
        else:
            url = f'{base_url}/{time_type}'
        
        item = "KRW-" + item

        # querystring = {"market":item, "count":int(period)}
        querystring = {"market":item, "to": to, "count":int(period)}
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, params=querystring)
        
        result = response.json()[::-1]

        return result

