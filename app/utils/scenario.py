import uuid
from exchange import bithumb


class Scenario():
    def __init__(self, name, order_currency):
        self._bithumb = bithumb.Bithumb(order_currency)
        self._name = name
        self._order_currency = order_currency

        self._scenario = {
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
            }    
        }

        for interval in ['1m', '3m', '5m', '10m', '30m', '1h', '6h', '12h', '24h']:

            self._scenario[f'{interval}'] = {
                order_currency: {
                    'get_orderbook': self.get_candlestick_iter(interval)
                }
            }
  
    def get_candlestick_iter(self, interval):
        
        return iter([{
            'ask': item['avg_price'], # The price when we get if we sell the item
            'bid': item['avg_price'], # The price when we have to pay the item
            # 'avg': item['avg_price'], # Average price
            'date': item['date'] # Date. What did you expect?
        } for item in self._bithumb.get_candlestick_current_interval(interval)])

    def get_orderbook(self):
        if self._name == 'sample':
            return self._bithumb.get_orderbook()
        else:
            return next(self._scenario[self._name][self._order_currency]['get_orderbook'])

    def trade_market_buy(self, units):
        return str(uuid.uuid1())

    def trade_market_sell(self, units):
        return str(uuid.uuid1())
