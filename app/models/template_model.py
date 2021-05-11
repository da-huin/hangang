class TemplateModel():
    def __init__(self, order_currency, test):
        self._order_currency = order_currency
        self._test = test

    def update(self, kind, data):
        if kind == 'orderbook':
            pass
        else:
            raise ValueError(f'invalid kind {kind}')

    def event(self, kind, data):
        if kind == 'transaction':
            if data['order']['kind'] == 'buy':
                pass

            elif data['order']['kind'] == 'sell':
                pass
            else:
                pass
        elif kind == 'command_failed':
            code = data['code']
            if data['kind'] == 'buy' and code == -1:
                pass
            else:
                pass

        else:
            raise ValueError(f'invalid kind {kind}')
