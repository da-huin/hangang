class Balance():
    def __init__(self, balance):
        self._balance = balance

    @property
    def balance(self):
        self._balance

    def add(self, amount):
        self._balance += amount
        return self._balance

    def sub(self, amount):
        if self._balance < 0:
            raise ValueError('The subtracted balance is less than 0.')
        self._balance -= amount
        return self._balance
    
    def sub_by_rate(self, rate):
        if rate >= 1:
            raise ValueError('rate is bigger than 1')
            
        amount = self._balance * rate
        self.sub(amount)

        return amount
