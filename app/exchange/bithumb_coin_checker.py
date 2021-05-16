import requests
from bs4 import BeautifulSoup
import json
import re
import time
from simple_utils import simple_logging as logging

class BithumbTickerCrawler():
    def __init__(self, retry_count = 10):
        self.retry_count = retry_count
        
    def request(self):
        headers = {'Cache-Control': 'no-cache'}
        url = 'https://pub1.bithumb.com/trade-info/v1/getTradeData?type=custom&crncCd=C0100&coin=C0101&lists=%7B%22ticker%22%3A%7B%22coinType%22%3A%22ALL%22%2C%22tickType%22%3A%22MID%22%7D%7D'
        for i in range(self.retry_count):
            try:

                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if data['error'] != '0000':
                    raise Exception(response)
                    
                ticker = data['data']['C0100']['ticker']
                
                return ticker                    
            except Exception as e:
                sleep_time = 2^(i + 1)
                logging.warning(f'retrying . . . {i + 1}({sleep_time})')
                logging.warning(e)
                # 2, 4, 8, 16, 32, 64, 128, . . .
                time.sleep(sleep_time)
                
                
        raise Exception('The request exceeded the limit.')
    
    def get_coin_ids(self):
        return list(self.request().keys())


class MBithumbCrawler():
    def __init__(self, retry_count=10):
        self.retry_count = retry_count
        
    def request(self):
        for i in range(self.retry_count):
            try:
                
                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

                response = requests.get('https://m.bithumb.com/', headers=headers)
                if response.status_code != 200:
                    raise Exception(response)

                html = response.text
                return html
            
            except Exception as e:
                sleep_time = 2^(i + 1)
                logging.warning(f'retrying . . . {i + 1}({sleep_time})')
                logging.warning(e)
                # 2, 4, 8, 16, 32, 64, 128, . . .
                time.sleep(sleep_time)
                
        raise Exception('The request exceeded the limit.')
        
    def print_variables(self, html):
        a = html[html.find('var COIN_DATA = '):]
        b = a[:a.find(';</script>')]

        for var_str in re.findall(r'var \w+ =', b):
            index = b.find(var_str)
            logging.info(var_str, index)
            
    def get_coins(self, html):
        a = html[html.find('var COIN '):]
        b = a[:a.find('var currencyRates')]
        v = b[b.find('{'):b.rfind('}') + 1]

        coins = {}
        for coin_id, p in json.loads(v)['C0100'].items():
            symbol_name = p['symbol_name']
            name = p['name']

            coins[coin_id] = {
                'symbol': symbol_name,
                'name': name,
                'coin_id': coin_id
            }

        return coins
    
    def get_coin_by_ids(self, html, coin_ids):
        mcoins = self.get_coins(html)
        
        return [mcoins[coin_id] for coin_id in coin_ids]

class BithumbCoinChecker():
    def __init__(self, test=False, interval=10, retry_count=10):
        logging.info('[BithumbCoinChecker] Ticker Crawler와 MBituhmb Crawler 인스턴스를 생성하는 중입니다.')
        self.ticker_crawler = BithumbTickerCrawler()
        self.mbithumb_crawler = MBithumbCrawler()
        self.retry_count = retry_count
        
        self.interval = interval
        self.test = test
        logging.info(f'[BithumbCoinChecker] 테스트 여부: {self.test}')
        logging.info(f'[BithumbCoinChecker] 요청 간격: {self.interval}')
        self.scenario = {
            'ids': iter([
                ['C0245', 'C0124', 'C0246', 'C0364'],
                ['C0245', 'C0124', 'C0246', 'C0364'],
                ['C0245', 'C0124', 'C0246'],
                ['C0245', 'C0124', 'C0246', 'C0276'],
                ['C0245', 'C0124', 'C0246', 'C0364'],
                
            ])
        }

        self.ids = self.get_coin_ids()

    def get_coin_ids(self):
        if not self.test:
            new_ids = self.ticker_crawler.get_coin_ids()
        else:
            new_ids = next(self.scenario['ids'], None)
        
        return new_ids

    def run(self, procedure):

        if not callable(procedure):
            raise ValueError('procedure type is not function.')
        

        logging.info(f'[BithumbCoinChecker][RUN] 실행중입니다.')

        count = 0
        while True:
            logging.info(f'[BithumbCoinChecker][RUN] ============================= {count}번 째 요청 처리중 =============================')
            new_ids = self.get_coin_ids()
            
            if not new_ids:
                logging.info('[BithumbCoinChecker][RUN] 테스트가 완료되었습니다.')
                break
                
            deleted_coins = set(self.ids) - set(new_ids)
            new_coins = set(new_ids) - set(self.ids)
            
            
            # 아이디 업데이트
            self.ids = new_ids
            
            
            # 코인은 변경되었지만 페이지에서 업데이트가 안 될 경우
            if len(new_coins) > 0 or len(deleted_coins) > 0:
                logging.info(f'[BithumbCoinChecker][RUN] 새로운 코인: {new_coins}')
                logging.info(f'[BithumbCoinChecker][RUN] 삭제된 코인: {deleted_coins}')
                
                success = False
                for i in range(self.retry_count):
                    try:
                        
                        # 신규 코인이 존재할 경우 procedure 실행
                        logging.info(f'[BithumbCoinChecker][RUN] 모바일 빗썸에서 코인 정보를 가져오는 중입니다.')

                        html = self.mbithumb_crawler.request()

                        if len(new_coins) > 0:
                            coins = self.mbithumb_crawler.get_coin_by_ids(html, new_coins)
                            procedure('new', coins)

                        if len(deleted_coins) > 0:
                            coins = self.mbithumb_crawler.get_coin_by_ids(html, deleted_coins)
                            procedure('deleted', coins)

                        success = True
                        break

                    except KeyError as e:
                        sleep_time = 2^(i + 1)
                        logging.warning(f'retrying . . . {i + 1}({sleep_time})')
                        logging.warning(e)
                        # 2, 4, 8, 16, 32, 64, 128, . . .
                        time.sleep(sleep_time)

                if not success:
                    raise Exception('The request exceeded the limit.')
            else:
                logging.info(f'[BithumbCoinChecker][RUN] 새로운 코인이나 삭제된 코인이 없습니다.')

                
            logging.info(f'[BithumbCoinChecker][RUN] {self.interval}초 대기 중입니다.')

            time.sleep(self.interval)
            count += 1

# def procedure(kind, coins):
#     if kind == 'new':
#         pass
#     elif kind == 'deleted':
#         pass
#     else:
#         raise ValueError(f'invalid kind {kind}')
        
#     logging.info(kind, coins)

# BithumbCoinChecker(test=False).run(procedure)