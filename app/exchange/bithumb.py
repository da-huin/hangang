import datetime
import aws_glove
import ccxt
import requests
import time
import boto3
import json

class Bithumb():
    def __init__(self, order_currency):
        self.order_currency = order_currency
        self._ssm = aws_glove.client('ssm', region_name='ap-northeast-2')
        auth = json.loads(self._ssm.get_parameter('/bitcoin/api/bithumb'))

        self._bithumb = ccxt.bithumb({
            'apiKey': auth['api_key'],
            'secret': auth['secret'],
            'verbose': False
        })

    def get_orderbook(self):
        payment_currency = 'KRW'
        response = requests.get(f'https://api.bithumb.com/public/orderbook/{self.order_currency}_{payment_currency}')
        data = response.json()['data']

        asks = data.get('asks', [])
        bids = data.get('bids', [])
        ask = int(asks[0]['price']) if len(asks) else -1
        bid = int(bids[0]['price']) if len(bids) else -1

        if ask == -1 or bid == -1:
            raise ValueError('cannot found ask or bid.')

        result = {
            'ask': ask,
            'bid': bid,
            'data': data
        }

        return result

    def trade_place_buy(self, units, price):
        return self._bithumb.private_post_trade_place({
            'order_currency': self.order_currency,
            'payment_currency': 'KRW',
            'units': units,
            'price': price,
            'type': 'ask'
        })

    def trade_place_sell(self, units, price):
        return self._bithumb.private_post_trade_place({
            'order_currency': self.order_currency,
            'payment_currency': 'KRW',
            'units': units,
            'price': price,
            'type': 'bid'            
        })

    def user_transactions(self, offset):
        response = self._bithumb.private_post_info_user_transactions({
            'offset': offset,
            'count': 50,
            'order_currency': self.order_currency,
            'payment_currency': 'KRW'
        }) 

        if response['status'] != '0000':
            raise Exception(f'response status is not 0000. \n {response}')

        return response['data']

    def private_post_info_orders(self):
        try:
            response = self._bithumb.private_post_info_orders({
                'order_currency': self.order_currency,
                'payment_currency': 'KRW'
            }) 
        except:
            return []

        return {item['order_id']: item for item in response['data']}

    def trade_market_buy(self, units):
        response = self._bithumb.private_post_trade_market_buy({
            'order_currency': self.order_currency,
            'payment_currency': 'KRW',
            'units': units
        })
        if response['status'] != '0000':
            raise Exception(f'response status is not 0000. \n {response}')

        return response['order_id']

    def trade_market_sell(self, units):
        response = self._bithumb.private_post_trade_market_sell({
            'order_currency': self.order_currency,
            'payment_currency': 'KRW',
            'units': units
        })
        if response['status'] != '0000':
            raise Exception(f'response status is not 0000. \n {response}')        

        return response['order_id']


    def get_candlestick_current_interval(self, interval):

        response = self._bithumb.public_get_candlestick_currency_interval({
            'currency': self.order_currency,
            'interval': interval
        })

        if response['status'] != '0000':
            raise Exception(f'response status is not 0000. \n {response}')                


        data = []
        for mtimestamp, start_price, end_price, high_price, low_price, volume in response['data']:
            date = datetime.datetime.fromtimestamp(int(mtimestamp)/1000)
            avg_price = float((float(high_price) + float(low_price)) / 2)
            data.append({
                'avg_price': avg_price,
                'date': date
            })

        return data
            


            