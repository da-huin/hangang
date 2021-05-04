import simple_utils
import argparse
from exchange.bithumb import Bithumb
from simple_utils import simple_logging as logging
import argparse
import simple_utils
from models import wave_model
from utils.balance import Balance
from utils import tools
import time
from senario import Senario


class Hangang():
    def __init__(self, args):
        self.args = args
        if self.args.test:
            logging.info(f'[APP INIT] DEV 모드입니다.')
        else:
            logging.info(f'[APP INIT] PROD 모드입니다.')
        self._bithumb = Bithumb(self.args.order_currency)
        self.balance = Balance(self.args.balance)
        self.wait_seconds = 60 if not self.args.test else 1
        self._senario = Senario(self.args.senario_name, self.args.order_currency)
        self._model = self._get_model()

    @property
    def model(self):
        return self._model

    def _get_model(self):
        if self.args.model == 'wave':
            model = wave_model.WaveModel(self.args.order_currency)
        else:
            raise ValueError(f'invalid model {self.args.model}')

        return model

    def main(self):

        self.routine()

    def routine(self):
        index = 0
        while True:
            logging.info(
                f'[APP] ==================== {index} ====================')

            if not self.args.test:
                logging.info(f'[APP] 빗썸에서 데이터를 가져오는 중입니다.')
                orderbook = self._bithumb.get_orderbook()
            else:
                logging.info(f'[APP] 시나리오에서 데이터를 가져오는 중입니다.')
                orderbook = self._senario.get_orderbook()

            logging.info(f'[APP] 모델을 업데이트 하는 중입니다.')
            commands = self.model.update('orderbook', orderbook)

            orders = self.process_commands(commands)['orders']
            events = self.process_orders(orders)['events']

            for event in events:
                self.model.event(event['kind'], event['data'])

            logging.info(f'[APP] 다음 순환까지 {self.wait_seconds}초 대기 중입니다.')
            time.sleep(self.wait_seconds)

            logging.info('')

            index += 1

    def process_orders(self, orders):
        result = {
            'events': []
        }

        ongoing_orders = self._bithumb.private_post_info_orders()
        for order_id, order in orders.items():
            if order_id not in ongoing_orders:
                result['events'].append({
                    'kind': 'transaction',
                    'data': {
                        'order': order
                    }
                })

        return result

    def process_commands(self, commands):
        result = {
            'orders': {}
        }
        if len(commands):
            logging.info(f'[APP][COMMAND] 새로운 명령어 처리를 시작 중입니다.')
        else:
            logging.info(f'[APP][COMMAND] 새로운 명령어가 없습니다.')

        for command in commands:
            kind = command['kind']
            logging.info(f'[APP][COMMAND][{kind}] 명령어를 처리하는 중입니다.')
            if kind == 'buy':

                amount = self.balance.sub_by_rate(command['rate'])
                logging.info(f'[APP][COMMAND][{kind}] {amount} 만큼 구매를 시도합니다.')

                # 빗썸 기본 수수료 0.25%
                minium_price = 1000 * 1.0025
                if amount < minium_price:
                    logging.info(
                        f'[APP][COMMAND][{kind}] 요구한 가격이 {minium_price}원 보다 적기 떄문에 취소되었습니다.')
                    self.model.event('command_fail', {
                        'command_kind': 'buy',
                        'code': -1
                    })
                else:
                    units = tools.get_units(amount, command['ask'])
                    if not self.args.test:
                        logging.info(f'[APP] 빗썸에 구매 요청을 보내는 중입니다.')
                        order_id = self._bithumb.trade_market_buy(units)
                    else:
                        logging.info(f'[APP] 시나리오에 구매 요청을 보내는 중입니다.')
                        order_id = self._senario.trade_market_buy(units)

                    result['orders'][order_id] = {
                        'order_id': order_id,
                        'units': units,
                        'kind': 'buy',
                        'price': command['ask']
                    }

            elif kind == 'sell':
                units = command['units']
                logging.info(f'[APP][COMMAND][{kind}] {units}(units) 만큼 판매를 시도합니다.')

                if not self.args.test:
                    logging.info(f'[APP] 빗썸에 판매 요청을 보내는 중입니다.')
                    order_id = self._bithumb.trade_market_sell(
                        units)
                else:
                    logging.info(f'[APP] 시나리오에 판매 요청을 보내는 중입니다.')
                    order_id = self._senario.trade_market_sell(
                        units)

                result['orders'][order_id] = {
                    'order_id': order_id,
                    'units': units,
                    'kind': 'sell',
                    'bid': command['bid'],
                    'ask': command['ask']                    
                }
            else:
                raise ValueError(f'invalid command {command}')

        return result


parser = argparse.ArgumentParser(description='hangang')
# parser.add_argument(
#     'action', help='The name of the command to be executed', type=str)
parser.add_argument('--model', help='model name', required=True)
parser.add_argument('--balance', help='balance', required=True, type=int)
parser.add_argument('--senario-name', help='senario name',
                    required=False, default='')
parser.add_argument('--test', action='store_true')
parser.add_argument('--order-currency', help='주문 통화(코인)', required=True)

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

Hangang(args).main()
