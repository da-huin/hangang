import argparse
import aws_glove
from simple_utils import simple_logging as logging
import dateutil
import requests
import datetime

class Cralwer():
    def __init__(self, args) -> None:
        self._args = args
        pass

    def bithumb_candlestick_1m(self, order_currency):
        gs3_lake = aws_glove.client('s3', bucket_name='items-lake')
        payment_currency = 'KRW'
        chart_intervals = '1m'

        url = f'https://api.bithumb.com/public/candlestick/{order_currency}_{payment_currency}/{chart_intervals}'
        response = requests.get(url)

        response.raise_for_status()

        data = response.json()['data']
        get_date = lambda p: datetime.datetime.fromtimestamp(p[0]/1000)
        first_dt = get_date(data[0])

        ampm = ''
        if first_dt.hour < 12:
            start_dt = datetime.datetime(year=first_dt.year, month=first_dt.month, day=first_dt.day, hour=12)
            end_dt = start_dt + dateutil.relativedelta.relativedelta(hour=12)
            ampm = 'pm'
            
        else:
            start_dt = datetime.datetime(year=first_dt.year, month=first_dt.month, day=first_dt.day, hour=0) + dateutil.relativedelta.relativedelta(days=1)
            end_dt = start_dt + dateutil.relativedelta.relativedelta(hour=12)
            ampm = 'am'

        data_to_be_stored = list(filter(lambda x: get_date(x) >= start_dt and get_date(x) < end_dt, data))

        filename = start_dt.strftime('%Y_%m_%d') + f'_{ampm}.json'
        s3_path = f'1.coin/bithumb/{order_currency}/{payment_currency}/{chart_intervals}/{filename}'.lower()

        gs3_lake.save(s3_path, data_to_be_stored)

        return s3_path

    def main(self):
        if self._args.crawler_name == 'bithumb-1m':
            # path = self.bithumb_candlestick_1m(self._args.order_currency)
            for order_currency in self._args.order_currency_list:
                path = self.bithumb_candlestick_1m(order_currency)
                logging.info(f'The {order_currency} crawling is complete. data has been stored in {path}')
        else:
            raise ValueError(f'invalid crawler name {self._args.crawler_name}')
        logging.info('All execution is complete.')

parser = argparse.ArgumentParser(description="""Hangang Crawler Example:  python3 crawler.py --crawler-name bithumb-1m --order-currency BTC""")
# parser.add_argument(
#     'action', help='The name of the command to be executed', type=str)
parser.add_argument('--crawler-name', help='availables: bithumb-1m', required=True)
parser.add_argument('--debug', action='store_true')
parser.add_argument('--order-currency', help='주문 통화(코인), 여러개일 경우 콤마로 구분해주세요.', required=True)


args = parser.parse_args()
args.order_currency_list = [v.strip() for v in args.order_currency.split(',') if v.strip()]

print("""
██╗  ██╗ █████╗ ███╗   ██╗ ██████╗  █████╗ ███╗   ██╗ ██████╗      ██████╗██████╗  █████╗ ██╗    ██╗██╗     ███████╗██████╗ 
██║  ██║██╔══██╗████╗  ██║██╔════╝ ██╔══██╗████╗  ██║██╔════╝     ██╔════╝██╔══██╗██╔══██╗██║    ██║██║     ██╔════╝██╔══██╗
███████║███████║██╔██╗ ██║██║  ███╗███████║██╔██╗ ██║██║  ███╗    ██║     ██████╔╝███████║██║ █╗ ██║██║     █████╗  ██████╔╝
██╔══██║██╔══██║██║╚██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║    ██║     ██╔══██╗██╔══██║██║███╗██║██║     ██╔══╝  ██╔══██╗
██║  ██║██║  ██║██║ ╚████║╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝    ╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝
""")

print(args)


if args.debug:
    logging._logger.setLevel(level=logging.logging.DEBUG)

Cralwer(args).main()