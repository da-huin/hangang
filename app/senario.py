import uuid


class Senario():
    def __init__(self, name, order_currency):
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

            }

        }

    def get_orderbook(self):
        return next(self._senario[self._name][self._order_currency]['get_orderbook'])

    def trade_market_buy(self, units):
        return str(uuid.uuid1())

    def trade_market_sell(self, units):
        return str(uuid.uuid1())
