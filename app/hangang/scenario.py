import uuid
from .exchange import upbit, bithumb
import datetime

class Scenario():
    def __init__(self, name, order_currency, scenario_price_type, target_date, candles):
        self._scenario_price_type = scenario_price_type
        self._bithumb = bithumb.Bithumb(order_currency)
        self._upbit = upbit.Upbit(order_currency)
        self._name = name
        self._order_currency = order_currency

        self._scenario = {}
        for exchange in ['bithumb', 'upbit']:
            if name.endswith(f'-{exchange}-backtest'):
                interval = name.replace(f'-{exchange}-backtest', '')

                self._scenario[name] = {
                    order_currency: {
                        'get_orderbook': self.get_candlestick_iter(exchange, interval, target_date=target_date, candles=candles)
                    }
                }

    def get_candlestick_iter(self, exchange, interval, target_date, candles):
        if exchange == 'bithumb':
            return iter([{
                'ask': item[self._scenario_price_type], # The price when we get if we sell the item
                'bid': item[self._scenario_price_type], # The price when we have to pay the item
                # 'avg': item['avg_price'], # Average price
                'date': item['date'] # Date. What did you expect?
            } for item in self._bithumb.get_candlestick_current_interval(interval)])
        elif exchange == 'upbit':

            
            result = []
            if interval.endswith('m'):
                data = self._upbit.get_candle('minute', self._order_currency, to=target_date, minute=interval[:-1])
            else:
                # 30d
                # 숫자, 영문 분할 -> 영문으로 tiem type 넣고, 숫자로 period 넣음
                short_time_type = interval[-1]
                time_type = ''
                if short_time_type == 'd':
                    time_type = 'days'
                elif short_time_type == 'M':
                    time_type = 'months'
                elif short_time_type == 'w':
                    time_type = 'weeks'
                else:
                    raise ValueError(f'invalid time type "{short_time_type}"')

                data = self._upbit.get_candle(time_type, item=self._order_currency, to=target_date, period=candles)

            # elif interval.endswith('days'):
            #     period = self._upbit.get_candle_hour
            # else:
            #     raise ValueError(f'invalid interval {interval}')
            for item in data:
                result.append({
                    'ask': item['trade_price'],
                    'bid': item['trade_price'],
                    'date': item['candle_date_time_kst']
                })
            return iter(result)

        else:
            raise ValueError(f'invalid exchange {exchange}')


    def get_orderbook(self):
        if self._name == 'realtime':
            return self._bithumb.get_orderbook()
        else:
            return next(self._scenario[self._name][self._order_currency]['get_orderbook'])

    def trade_market_buy(self, units):
        return str(uuid.uuid1())

    def trade_market_sell(self, units):
        return str(uuid.uuid1())
