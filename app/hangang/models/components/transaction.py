class OrderItem():
    def __init__(self, kind, info, message=''):
        self._kind = kind
        self._info = info
        self._status = 0
        self._message = message

    @property
    def kind(self):
        return self._kind

    @property
    def get(self, key):
        if key not in self._info:
            raise ValueError(f'{key} is not in info.')

        return self.info[key]

    def is_success(self):
        return self._status == 1

    def is_failed(self):
        return self._status == -1

    def is_complete(self):
        return self._status != 0

    def success(self):
        self._status = 1

    def fail(self):
        self._status = -1


class Order():
    def __init__(self) -> None:
        self._orders = []

    def pop(self):
        orders = self._orders.copy()
        self._orders.clear()

        return orders

    def sell_by_units(self, units, message='판매'):
        data = {
            'units': units
        }

        self._orders.append(OrderItem('sell', data, message=message))

    def buy_at_rate(self, rate, message='구매'):
        data = {
            'rate': rate
        }
        
        self._orders.append(OrderItem('buy', data, message=message))

class Command():
    def __init__(self) -> None:
        self._order = Order()

    @property
    def order(self):
        return self._order
        
    