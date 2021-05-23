import numpy as np
import warnings
from collections import deque
# from simple_utils import simple_logging as logging

class CMOModel():
    def __init__(self, order_currency, test, period):
        self._order_currency = order_currency # This is not needed. We are going to transact multiple types of digital assets.
        self._test = test # Test flag argument.
        self._period = period # CMO period.
        self._dq = deque(maxlen=period + 1)
        self._watchlist = 0

        self._tr_flag = 0 # Has the model already bought the item?
        self._buy_price = np.nan
        self._quantity = np.nan

        self._momentum = np.nan # Momentum flag. The indicator that the market keeps going in current direction (bullish/bearish).

    def update(self, market_data):
        '''
        Update current market data.
        Return order (to be given the market).
        market_data: Consists of ask, bid ...
        '''

        ask = market_data['ask']
        # bid = market_data['bid']

        cmo_prev = np.nan
        cmo_curr = np.nan
        order_list = []

        self._dq.append(ask)
        
        if len(self._dq) == self._period + 1:

            prices = list(self._dq)
            
            
            prices_prev = prices[:-1]
            prices_curr = prices[1:]

            cmo_prev = self.calc_cmo(prices_prev)
            cmo_curr = self.calc_cmo(prices_curr)
            
            self._dq.popleft()

        if self._tr_flag == 0: # Trying to buy
            if cmo_curr > -50 and self._watchlist == 1: # Error case
                self._watchlist = 0

            if cmo_curr <= -50 and self._watchlist == 0:
                self._watchlist = 1 # Set to watchlist

            elif cmo_curr <= -50 and self._watchlist == 1:
                if cmo_prev >= cmo_curr and np.isnan(self._momentum):
                    # The price keeps going down. We're not gonna buying that.
                    self._momentum = 1

                elif cmo_prev < cmo_curr and self._momentum == 1:
                    # The price has gone up just one time. But is the market really bullish?
                    # We are not sure. So we're gonna watch one more time.
                    self._momentum = 0

                elif cmo_prev < cmo_curr and self._momentum == 0:
                    # Okay, the price is going up. Let's buy the item!
                    order = {
                        'kind': 'buy',
                        'rate': 1,
                        # 'ask': ask,
                        'message': 'buy'
                    }
                    # logging.debug(f'CURRENT CMO: {cmo_curr}')
                    self._watchlist = 0 # Back to normal
                    self._momentum = np.nan
                    order_list.append(order)
                elif cmo_prev >= cmo_curr:
                    pass

        elif self._tr_flag == 1: # Hold? Drop?
            if cmo_curr >= 50 and self._watchlist == 0:
                self._watchlist = 1
            
            elif cmo_curr >= 50 and self._watchlist == 1:
                if cmo_prev <= cmo_curr and cmo_curr != 100:
                    pass
                elif cmo_prev > cmo_curr or cmo_curr == 100:
                    if cmo_curr == 100:
                        pass
                    else:
                        order = {
                        'kind': 'sell',
                        'units': self._quantity,
                        # 'bid': bid,
                        # # 정보제공용 
                        # 'ask': ask,
                        'message': 'sell'
                    }
                    # logging.debug(f'CURRENT CMO: {cmo_curr}')
                    self._watchlist = 0
                    order_list.append(order)
            # elif 0.9 * self._buy_price < market_data['ask']:
            #     order = {
            #             'kind': 'sell',
            #             'units': self._quantity,
            #             # 'bid': bid,
            #             # # 정보제공용 
            #             # 'ask': ask,
            #             'message': 'sell'
            #         }
            #     self._watchlist = 0
            #     order_list.append(order)


        return order_list

    def event(self, tr_type, event_data):
        '''
        Main function inform this model of what kind of transaction has been made.
        
        tr_type: type of transaction {buy, sell, command_failed, ...}
        event_data: More detailed data about the transaction. Refer to readme.md for more information.
        '''
        
        # order_data looks like as follows:
        # "kind": "buy",
        # "order_id": "거래소에 요청한 후 받은 주문번호",
        # "units": "수량",
        # "price": "구매 요청 가격",
        # "message": "모델에서 구매 요청시에 보낸 메세지"

        # temp = dict()
        if tr_type == 'transaction':
            order_data = event_data['order']
            event_kind = order_data['kind']
            if event_kind == 'buy':
                # Save price, quantity, and value
                # temp = {
                #     'units': order_data['units'],
                #     'price': order_data['price'],
                #     'value': order_data['units'] * order_data['price']
                # }
                
                self._tr_flag = 1
                self._buy_price = order_data['price']
                self._quantity = order_data['units']

            elif event_kind == 'sell':
                # temp.clear()
                self._tr_flag = 0
                self._buy_price = np.nan
            else:
                raise ValueError(f'invalid event kind {event_kind}')
        elif tr_type == 'command_failed':
            code = event_data['code']
            if code == -1:
                pass
            else:
                pass
        else:
            raise ValueError(f'invalid type {tr_type}')


    # Using a queue, we can calculate previous CMO and CMO now
    def calc_cmo(self, data):
        '''
        Calculate CMO.\n
        CMO stands for Chande Momentum Oscillator.\n

        data: Market close data over N period of time.
        '''
        data = np.array(data)
        sum_ups = []
        sum_downs = []

        for i in range(1, self._period):
            diff = data[i] - data[i-1]
            if diff > 0:
                sum_ups.append(diff)
            elif diff < 0:
                sum_downs.append(abs(diff))

        sum_ups = sum(sum_ups)
        sum_downs = sum(sum_downs)

        if sum_ups == 0 and sum_downs == 0:
            cmo = np.nan
        else:
            cmo = 100 * ( (sum_ups - sum_downs) / (sum_ups + sum_downs) )

        return cmo

    # Legacy method
    def get_cmo_base(self, data, period):
        '''
        Get all the pervious CMOs.
        '''

        data = np.array(data)
        moving_period_diffs = [[(data[idx+1-period:idx+1][i] -
                 data[idx+1-period:idx+1][i-1]) for i in range(1, len(data[idx+1-period:idx+1]))] for idx in range(0, len(data))]

        sum_up = []
        sum_down = []

        for period_diffs in moving_period_diffs:
            ups = [val if val > 0 else 0 for val in period_diffs]
            sum_up.append(sum(ups))
            downs = [abs(val) if val < 0 else 0 for val in period_diffs]
            sum_down.append(sum(downs))
        
        sum_up = np.array(sum_up)
        sum_down = np.array(sum_down)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
        cmo = 100 * ((sum_up - sum_down) / (sum_up + sum_down))

        if cmo > 0:
            cmo = min(100, cmo)
        elif cmo < 0:
            cmo = max(-100, cmo)

        return cmo