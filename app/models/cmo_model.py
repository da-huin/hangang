import numpy as np

class CMO():
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

    def get_cmo(self, data):
        '''
        Get current CMOs.  
        Only calculate 4 digital assets based on volumes.
        '''
        # CMO means Chande Momentum Oscillator.

        cmo = np.array([np.nan, np.nan, np.nan, np.nan])

        return cmo

    def transact(self, cmo, data):
        '''
        This model decides whether our model buys/sells the item.
        '''
        # Idea: 2% return vs >= 50 cmo?
        cmo = self.get_cmo(data)


        watchlist = np.array([0,0,0,0]) # Watchlist flag. watchlist[i] = {0, 1}
        # 0 means the model is not considering buying the item. 1 means the model is looking for opportunity.
        cnt = np.array([0,0,0,0])
        # Upbit exchange API allows 15/s requests for non-orders. If cnt[i] = 15, it means 1 second has passed.
        for i in range(4):
            # Ideally, each of these conditional statements should be visited 15 times per second.
            curr_cmo = self.get_cmo(data)
            if cmo[i] <= -50 & watchlist[i] == 0:
                watchlist[i] = 1

            elif cmo[i] <= -50 & watchlist[i] == 1:
                if cmo[i] >= curr_cmo[i]: # Refresh CMO in order to reduce risks
                    cmo[i] = curr_cmo[i]
                else:
                    if cnt[i] == 75: # Wait 5 seconds
                        pass # Buy
                    else:
                        cnt[i] += 1

            elif cmo[i] >= 50 & watchlist[i] == 0:
                watchlist[i] = 1
            
            elif cmo[i] >= 50 & watchlist[i] == 1:
                if cmo[i] <= curr_cmo[i]:
                    cmo[i] = curr_cmo[i]
                else:
                    if cnt[i] == 75:
                        pass # Sell
                    else:
                        cnt[i] += 1