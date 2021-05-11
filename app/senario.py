import uuid
from exchange import bithumb


class Senario():
    def __init__(self, name, order_currency):
        self._bithumb = bithumb.Bithumb(order_currency)
        self._name = name
        self._order_currency = order_currency

        self._senario = {
            'sample': {
                order_currency: {
                    'get_orderbook': iter([{
                        'ask': 8195,
                        'bid': 8185,
                    },
                        # {
                        #     'ask': 8185,
                        #     'bid': 8175
                        # },
                        # {

                        #     'ask': 8300,
                        #     'bid': 8230
                        # },
                        # {
                        #     'ask': 8000,
                        #     'bid': 7950
                        # },
                        {
                        'ask': 7500,
                        'bid': 7480
                    }, {
                        'ask': 7500,
                        'bid': 7480
                    }, {
                        'ask': 8500,
                        'bid': 8490
                    }, {
                        'ask': 6000,
                        'bid': 5980
                    },  {
                        'ask': 6000,
                        'bid': 5980
                    },  {
                        'ask': 6300,
                        'bid': 6290
                    },  {
                        'ask': 5900,
                        'bid': 5890
                    }])
                }
            },
            '30m-backtest': {
                order_currency: {
                    'get_orderbook': self.get_candlestick_iter('30m')
                }
            },
            '24h-backtest': {
                order_currency: {
                    'get_orderbook': self.get_candlestick_iter('24h')
                }                
            },
            '3m-backtest': {
                order_currency: {
                    'get_orderbook': self.get_candlestick_iter('3m')
                }                
            },
            '10m-backtest': {
                order_currency: {
                    'get_orderbook': self.get_candlestick_iter('10m')
                }                
            }                     
        }

    def get_candlestick_iter(self, interval):
        return iter([{
            'ask': item['avg_price'] + 10, # The price when we get if we sell the item
            'bid': item['avg_price'] - 10, # The price when we have to pay the item
            'avg': item['avg_price'], # Average price
            'date': item['date'] # Date. What did you expect?
        } for item in self._bithumb.get_candlestick_current_interval(interval)])

    def get_orderbook(self):
        if self._name == 'sample':
            return self._bithumb.get_orderbook()
        else:
            return next(self._senario[self._name][self._order_currency]['get_orderbook'])

    def trade_market_buy(self, units):
        return str(uuid.uuid1())

    def trade_market_sell(self, units):
        return str(uuid.uuid1())
