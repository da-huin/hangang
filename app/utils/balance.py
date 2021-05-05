class Balance():
    def __init__(self, balance=0, units=0):
        self._balance = balance
        self._units = units

    def __str__(self):
        return str(f'Blance: {self._balance}, Units: {self._units}')
    
    @property
    def balance(self):
        self._balance

    def add(self, amount):
        self._balance += amount
        return self._balance

    def sub(self, amount):
        self._balance -= amount
        return self._balance
    
    def get_balance_by_rate(self, rate):

        if rate >= 1:
            raise ValueError('rate is bigger than 1')
            
        amount = int(self._balance * rate)

        return amount

    def add_units(self, units):
        self._units += units
        return self._units

    def sub_units(self, units):
        self._units -= units

        return self._units
