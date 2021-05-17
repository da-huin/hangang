class OrderItem():
    def __init__(self, kind):
        self._kind = kind
        self._status = 0
        self._code = 0

    @property
    def kind(self):
        return self._kind

    def set(self, key, value):
        self._data[key] = value
        
    def is_success(self):
        return self._status == 1

    def is_failed(self):
        return self._status == -1

    def is_ongoing(self):
        return self._status == 2
        
    def is_complete(self):
        return self.is_failed() or self.is_success()

    def ongoing(self):
        self._status = 2

    def success(self):
        self._status = 1

    def fail(self, code):
        self._status = -1
        self._code = code


class SellOrderItem(OrderItem):
    def __init__(self):
        self._units = None
        self._bid = None
        self._order_id = None        
        super().__init__('sell')

    @property
    def units(self):
        return self._units

    @property
    def bid(self):
        return self._bid

    @property
    def order_id(self):
        return self._order_id

    def sell_by_units(self, units):
        self._units = units

    def ongoing(self, order_id, bid):
        self._bid = int(bid)
        self._order_id = order_id

        super().ongoing()

class BuyOrderItem(OrderItem):
    def __init__(self):
        self._units = None
        self._ask = None
        self._order_id = None
        self._rate = None
        super().__init__('buy')
    

    @property
    def units(self):
        return self._units

    @property
    def ask(self):
        return self._ask

    @property
    def order_id(self):
        return self._order_id

    @property
    def rate(self):
        return self._rate

    def buy_at_rate(self, rate):
        self._rate = rate

    def ongoing(self, order_id, ask, units):
        self._ask = int(ask)
        self._order_id = order_id
        self._units = units

        super().ongoing()
        

class Order():
    def __init__(self) -> None:
        self._orders = []

    def all(self):
        return self._orders

    def clear(self):
        return self._orders.clear()

    def pop(self):
        orders = self._orders.copy()
        self._orders.clear()

        return orders

    def sell_by_units(self, units):
        sell_order_item = SellOrderItem()
        sell_order_item.sell_by_units(units)
        self._orders.append(sell_order_item)

    def buy_at_rate(self, rate):
        buy_order_item = BuyOrderItem()
        buy_order_item.buy_at_rate(rate)
        self._orders.append(buy_order_item)

class Command():
    def __init__(self) -> None:
        self._order = Order()

    @property
    def order(self):
        return self._order
        
    