class Balance():
    def __init__(self, balance=0, units=0):
        self._balance = balance
        self._units = units

    def get_balance_string(self, price):
        amount_str = format(self.get_amount(price), ',') + '원'
        return f'지갑(현금): {format(self.balance, ",")}원 지갑(코인): {self.units} 총액: {amount_str}'
        
    @property
    def balance(self):
        return self._balance
    
    @property
    def units(self):
        return self._units

    def add(self, amount):
        self._balance += amount
        return self._balance

    def sub(self, amount):
        self._balance -= amount
        return self._balance
    
    def get_balance_by_rate(self, rate):

        if rate > 1:
            raise ValueError('rate is bigger than 1')
            
        amount = int(self._balance * rate)

        return amount

    def add_units(self, units):
        self._units += units
        return self._units

    def sub_units(self, units):
        self._units -= units

        return self._units

    def get_amount(self, price):
        """
        price: 시세
        """
        return int(self.balance + self.units * price)
        



