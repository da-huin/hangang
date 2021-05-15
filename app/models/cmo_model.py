import numpy as np
import warnings

class CMO():
    def __init__(self, order_currency, test):
        self._order_currency = order_currency # This is not needed. We are going to transact multiple types of digital assets.
        self._test = test # Test flag argument.

    def update(self, type, data):
        if type == 'orderbook':
            pass
        else:
            raise ValueError(f'Invalid type {type}')

        return command

    def event(self, type, data):
        if type == 'transaction':
            if data['order']['type'] == 'buy':
                pass

            elif data['order']['type'] == 'sell':
                pass
            else:
                pass
        elif type == 'command_failed':
            code = data['code']
            if data['type'] == 'buy' and code == -1:
                pass
            else:
                pass

        else:
            raise ValueError(f'invalid type {type}')

    def calc_ccmo(self, data, price, period):
        '''
        Calculate current CMO.\n
        CMO stands for Chande Momentum Oscillator.\n

        data: (period - 1) previous closes.
        price: Current price of the item.  
        '''
        # Fetch (period - 1) previous closes (-> data)
        # Append current price to the data
        # Calculate CMO
        data = np.array(data)
        data = np.append(data, price)
        sum_ups = []
        sum_downs = []

        for i in range(1, period):
            diff = data[i] - data[i-1]
            if diff > 0:
                sum_ups.append(diff)
            elif diff < 0:
                sum_downs.append(abs(diff))

        sum_ups = sum(sum_ups)
        sum_downs = sum(sum_downs)

        cmo = 100 * ( (sum_ups - sum_downs) / (sum_ups + sum_downs) )

        return cmo

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

    def transact(self, cmo, data):
        '''
        This model decides whether our model buys/sells the item.\n
        Choose n items -> get market data of those items.\n
        -> Calculate CMOs -> transact
        '''

        # Idea: 2% return vs >= 50 cmo?
        cmo_prev = self.get_cmo(data)


        watchlist = np.array([0,0,0,0]) # Watchlist flag. watchlist[i] = {0, 1}
        # 0 means the model is not considering buying the item. 1 means the model is looking for opportunity.
        cnt = np.array([0,0,0,0])
        # Upbit exchange API allows 15/s requests for non-orders. If cnt[i] = 15, it means 1 second has passed.
        for i in range(4):
            # Ideally, each of these conditional statements should be visited 15 times per second.
            cmo_curr = self.get_cmo(data)

            if cmo[i] <= -50 & watchlist[i] == 0:
                watchlist[i] = 1

            elif cmo[i] <= -50 & watchlist[i] == 1:
                if cmo[i] >= cmo_curr[i]: # Refresh CMO in order to reduce risks
                    cmo[i] = cmo_curr[i]
                else:
                    if cnt[i] == 75: # Wait 5 seconds
                        pass # Buy
                    else:
                        cnt[i] += 1

            elif cmo[i] >= 50 & watchlist[i] == 0:
                watchlist[i] = 1
            
            elif cmo[i] >= 50 & watchlist[i] == 1:
                if cmo[i] <= cmo_curr[i]:
                    cmo[i] = cmo_curr[i]
                else:
                    if cnt[i] == 75:
                        pass # Sell
                    else:
                        cnt[i] += 1