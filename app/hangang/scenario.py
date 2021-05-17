import uuid
from .exchange import bithumb


class Scenario():
    def __init__(self, name, order_currency):
        self._bithumb = bithumb.Bithumb(order_currency)
        self._name = name
        self._order_currency = order_currency

        self._scenario = {}
        if name.endswith('-bithumb-backtest'):
            interval = name.replace('-bithumb-backtest', '')

            self._scenario[name] = {
                order_currency: {
                    'get_orderbook': self.get_candlestick_iter(interval)
                }
            }
  
    def get_candlestick_iter(self, interval):
        
        return iter([{
            'ask': item['end_price'], # The price when we get if we sell the item
            'bid': item['end_price'], # The price when we have to pay the item
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
