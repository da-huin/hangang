import traceback
import simple_utils
import argparse
from .exchange.bithumb import Bithumb
from simple_utils import simple_logging as logging
import argparse
import simple_utils
from .models import wave_model
from .models import cmo_model
from .utils.balance import Balance
from .utils import tools
import time
from .scenario import Scenario




class Hangang():
    def __init__(self, args):
        self.args = args
        if self.args.test:
            logging.info(f'[APP INIT] DEV 모드입니다.')
        else:
            logging.info(f'[APP INIT] PROD 모드입니다.')
        self._bithumb = Bithumb(self.args.order_currency)
        self.balance = Balance(self.args.balance)
        self.wait_seconds = self.args.wait_seconds
        self._scenario = Scenario(self.args.scenario_name, self.args.order_currency)
        self._model = self._get_model()
        

    @property
    def model(self):
        return self._model

    def _get_model(self):
        if self.args.model == 'wave':
            model = wave_model.WaveModel(order_currency=self.args.order_currency, test=self.args.test)
        elif self.args.model == 'cmo':
            model = cmo_model.CMOModel(order_currency=self.args.order_currency, test=self.args.test, period=self.args.period)
        else:
            raise ValueError(f'invalid model {self.args.model}')

        return model

    def main(self):
        self.routine()

    def routine(self):
        index = 0
        last_orderbook = None
        while True:
            logging.debug(
                f'[APP][ROUTINE] ==================== {index} ====================')

            logging.debug(f'[APP][ROUTINE] 잔고: {self.balance}')

            if not self.args.test:
                logging.debug(f'[APP][ROUTINE] 빗썸에서 데이터를 가져오는 중입니다.')
                orderbook = self._bithumb.get_orderbook()
            else:
                logging.debug(f'[APP][ROUTINE] 시나리오에서 데이터를 가져오는 중입니다.')
                try:
                    orderbook = self._scenario.get_orderbook()
                    last_orderbook = orderbook
                except StopIteration:
                    logging.info(f'잔고: {self.balance} 총액: {format(int(self.balance.balance + self.balance.units * last_orderbook["bid"]), ",")}원')
                    break
                    
            
            # if (self.args.test and index % 10 == 0):
                # date = orderbook.get('date', '')
            date = orderbook.get('date', '')
            logging.info(f'[APP][ROUTINE] orderbook date: {date}.')
            logging.debug(f'[APP][ROUTINE] 모델을 업데이트 하는 중입니다.')
            commands = self.model.update(orderbook)
            orders = self.process_commands(commands, orderbook)['orders']
            events = self.process_orders(orders)['events']

            for event in events:
                self.model.event(event['kind'], event['data'])

            logging.debug(f'[APP][ROUTINE] 다음 순환까지 {self.wait_seconds}초 대기 중입니다.')
            time.sleep(self.wait_seconds)

            logging.debug('')

            index += 1

    def process_orders(self, orders):
        result = {
            'events': []
        }
        
        if not self.args.test:
            ongoing_orders = self._bithumb.private_post_info_orders()
        else:
            ongoing_orders = []
            
        for order_id, order in orders.items():
            if order_id not in ongoing_orders:
                result['events'].append({
                    'kind': 'transaction',
                    'data': {
                        'order': order
                    }
                })

                logging.info(f'[APP][ORDERS] 잔고: {self.balance}')
                logging.info(f'[APP][ORDERS] events: {order}')

        return result

    def process_commands(self, commands, orderbook):
        result = {
            'orders': {}
        }
        if len(commands):
            logging.debug(f'[APP][COMMAND] 새로운 명령어 처리를 시작 중입니다.')
        else:
            logging.debug(f'[APP][COMMAND] 새로운 명령어가 없습니다.')

        for command in commands:
            kind = command['kind']
            logging.debug(f'[APP][COMMAND][{kind}] 명령어를 처리하는 중입니다.')
            if kind == 'buy':

                amount = int(self.balance.get_balance_by_rate(command['rate']))
                # amount = self.balance.sub_by_rate(command['rate'])
                logging.debug(f'[APP][COMMAND][{kind}] {amount} 만큼 구매를 시도합니다.')

                # 빗썸 기본 수수료 0.25%
                minium_price = 1000 * 1.0025
                if amount < minium_price:
                    logging.debug(
                        f'[APP][COMMAND][{kind}] 요구한 가격이 {minium_price}원 보다 적기 떄문에 취소되었습니다.')
                    self.model.event('command_failed', {
                        'code': -1
                    })
                else:
                    units = tools.get_units(amount, orderbook['ask'])
                    if not self.args.test:
                        logging.debug(f'[APP] 빗썸에 구매 요청을 보내는 중입니다.')
                        order_id = self._bithumb.trade_market_buy(units)
                    else:
                        logging.debug(f'[APP] 시나리오에 구매 요청을 보내는 중입니다.')
                        order_id = self._scenario.trade_market_buy(units)

                    self.balance.sub(amount)
                    self.balance.add_units(units)

                    result['orders'][order_id] = {
                        'order_id': order_id,
                        'units': units,
                        'kind': 'buy',
                        'price': orderbook['ask'],
                        'message': command['message']
                    }

            elif kind == 'sell':
                units = command['units']
                logging.debug(f'[APP][COMMAND][{kind}] {units}(units) 만큼 판매를 시도합니다.')

                if not self.args.test:
                    logging.debug(f'[APP] 빗썸에 판매 요청을 보내는 중입니다.')
                    order_id = self._bithumb.trade_market_sell(
                        units)
                else:
                    logging.debug(f'[APP] 시나리오에 판매 요청을 보내는 중입니다.')
                    order_id = self._scenario.trade_market_sell(
                        units)

                self.balance.add(tools.get_krw(units, orderbook['bid']))
                self.balance.sub_units(units)
                # if orderbook['bid'] < 0:
                #     print(orderbook)
                #     exit(0)
                result['orders'][order_id] = {
                    'order_id': order_id,
                    'units': units,
                    'kind': 'sell',
                    'price': orderbook['bid'],
                    'ask': orderbook['ask'],
                    'message': command['message']
                }
            else:
                raise ValueError(f'invalid command {command}')
        
        return result


parser = argparse.ArgumentParser(description="""
Hangang Example:  python3 app.py --model wave --balance 1000000 --scenario-name 3m --test --debug --order-currency BTC --wait-seconds 1
""")
# parser.add_argument(
#     'action', help='The name of the command to be executed', type=str)
parser.add_argument('--model', help='model name', required=True)
parser.add_argument('--balance', help='balance', required=True, type=int)
parser.add_argument('--scenario-name', help='scenario name',
                    required=False, default='')
parser.add_argument('--test', action='store_true')
parser.add_argument('--debug', action='store_true')
parser.add_argument('--order-currency', help='주문 통화(코인)', required=True)
parser.add_argument('--wait-seconds', help='대기 시간', default=60, type=float)
parser.add_argument('--period', help='CMO 모델에서 사용하는 매개변수', default=6, type=int)



args = parser.parse_args()
print("""
██╗  ██╗ █████╗ ███╗   ██╗ ██████╗  █████╗ ███╗   ██╗ ██████╗ 
██║  ██║██╔══██╗████╗  ██║██╔════╝ ██╔══██╗████╗  ██║██╔════╝ 
███████║███████║██╔██╗ ██║██║  ███╗███████║██╔██╗ ██║██║  ███╗
██╔══██║██╔══██║██║╚██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║
██║  ██║██║  ██║██║ ╚████║╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
""")

print(args)

if args.debug:
    logging._logger.setLevel(level=logging.logging.DEBUG)

Hangang(args).main()
