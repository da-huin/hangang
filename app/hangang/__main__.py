import traceback
import simple_utils
import argparse
from .exchange.bithumb import Bithumb
from simple_utils import simple_logging as logging
import argparse
import simple_utils
from .models import wave_model
from .models import cmo_model
from .models import cmo_model_v1
from .utils.balance import Balance
from .utils import tools
import time
from .scenario import Scenario
from .models.components.structure import SellOrderItem, BuyOrderItem
import datetime

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
        self._scenario = Scenario(self.args.scenario_name, self.args.order_currency, self.args.scenario_price_type)
        self._model = self._get_model()


    @property
    def model(self):
        return self._model

    def _get_model(self):
        if self.args.model == 'wave':
            if not self.args.test:
                raise ValueError('wave 모델로는 테스트만 가능합니다.')

            model = wave_model.WaveModel(order_currency=self.args.order_currency, test=self.args.test)
        elif self.args.model == 'cmo':
            model = cmo_model.CMOModel(order_currency=self.args.order_currency, test=self.args.test, period=self.args.period)
        elif self.args.model == 'cmo_v1':
            model = cmo_model_v1.CMOModel(order_currency=self.args.order_currency, test=self.args.test, period=self.args.period)
        else:
            raise ValueError(f'invalid model {self.args.model}')

        return model

    def main(self):
        self.routine()

    def routine(self):
        index = 0
        last_orderbook = None
        first = True

            

            
        while True:
       
            logging.debug(
                f'[APP][ROUTINE] ==================== {index} ====================')

            logging.debug(f'[APP][ROUTINE] 잔고: {self.balance}')

            if not first:            
                logging.info(f'[APP][ROUTINE] 다음 순환까지 {self.wait_seconds}초 대기 중입니다.')
            # 1분 이상 단위일 때 00초에서 실행
            if self.wait_seconds >= 60:
                if not first:
                    time.sleep(self.wait_seconds - 30)
                logging.info(f'[APP][ROUTINE] 0초가 될 때까지 대기하는 중입니다.')
                while True:
                    if datetime.datetime.now().second == 0:
                        print(datetime.datetime.now())
                        break
                    time.sleep(0.1)
            else:
                if not first:
                    time.sleep(self.wait_seconds)

            if not self.args.test:
                logging.debug(f'[APP][ROUTINE] 빗썸에서 데이터를 가져오는 중입니다.')
                orderbook = self._bithumb.get_orderbook()
            else:
                logging.debug(f'[APP][ROUTINE] 시나리오에서 데이터를 가져오는 중입니다.')
                try:
                    orderbook = self._scenario.get_orderbook()
                    last_orderbook = orderbook
                except StopIteration:
                    logging.info(self.balance.get_balance_string(last_orderbook['bid']))
                    break

            date = orderbook.get('date', '')
            ask = orderbook['ask']
            bid = orderbook['bid']

            # 예: 1830 -> 1790
            # 구매시: 실제 시세보다 높음
            ask += ask * (self.args.commission_rate / 100)
            # 판매시: 실제 시세보다 낮음
            bid -= bid * (self.args.commission_rate / 100)

            logging.info(f'[APP][ROUTINE] {self.args.order_currency} | {date} | {ask} | {bid}')
            logging.debug(f'[APP][ROUTINE] 모델을 업데이트 하는 중입니다.')
            command = self.model.update(ask, bid)
            command = self.process_command(command, ask, bid)
            self.send_events(command)



            first = False

            index += 1

    def send_events(self, command):

        events = []
        if not self.args.test:
            ongoing_orders = self._bithumb.private_post_info_orders()
        else:
            ongoing_orders = []

        for order_item in command.order.all():
            if order_item.order_id not in ongoing_orders:
                if order_item.is_failed():
                    logging.info(f'[APP][SEND_EVENTS] 명령어 실패 코드: {order_item.code}')
                else:
                    order_item.success()
                    if isinstance(order_item, BuyOrderItem):
                        logging.info(f'[APP][SEND_EVENTS][구매] 구매가격: {format(order_item.ask, ",")}원 수량: {order_item.units}')
                        logging.info(f'[APP][SEND_EVENTS][구매] {self.balance.get_balance_string(order_item.ask)}')

                    elif isinstance(order_item, SellOrderItem):
                        logging.info(f'[APP][SEND_EVENTS][판매] 판매가격: {format(order_item.bid, ",")}원 수량: {order_item.units}')
                        logging.info(f'[APP][SEND_EVENTS][판매] {self.balance.get_balance_string(order_item.bid)}')
                    else:
                        raise ValueError(f'invalid kind {type(order_item)}')                
                self.model.event('order', order_item)

        return events

    def process_command(self, command, ask, bid):
        for order_item in command.order.all():
            
            logging.debug(f'[APP][COMMAND][{order_item.kind}] 명령어를 처리하는 중입니다.')
            if order_item.kind == 'buy':
                amount = int(self.balance.get_balance_by_rate(order_item.rate))
                logging.debug(f'[APP][COMMAND][{order_item.kind}] {amount} 만큼 구매를 시도합니다.')

                # 빗썸 기본 수수료 0.25%
                minium_price = 1000 * (1 + (self.args.commission_rate / 100))
                if amount < minium_price:
                    logging.info(
                        f'[APP][COMMAND][{order_item.kind}] 요구한 가격({amount}원)이 최소가격({minium_price}원) 보다 적기 떄문에 취소되었습니다.')
                    order_item.fail(code=-1)
                else:
                    units = tools.get_units(amount, ask)
                   
                    if not self.args.test:
                        # logging.info(f'[APP][COMMAND] 빗썸에 구매 요청을 보내지 않았습니다.')
                        # order_id = 1
                        logging.info(f'[APP][COMMAND] 빗썸에 구매 요청을 보내는 중입니다.')
                        order_id = self._bithumb.trade_market_buy(units)
                    else:
                        logging.info(f'[APP][COMMAND] 시나리오에 구매 요청을 보내는 중입니다.')
                        order_id = self._scenario.trade_market_buy(units)

                    self.balance.sub(amount)
                    self.balance.add_units(units)
  
                    order_item.ongoing(order_id=order_id, ask=ask, units=units)

            elif order_item.kind == 'sell':
                logging.debug(f'[APP][COMMAND][{order_item.kind}] {order_item.units}(units) 만큼 판매를 시도합니다.')

                if not self.args.test:
                    # logging.info(f'[APP][COMMAND] 빗썸에 판매 요청을 보내지 않았습니다.')
                    # order_id = 1
                    logging.info(f'[APP][COMMAND] 빗썸에 판매 요청을 보내는 중입니다.')
                    order_id = self._bithumb.trade_market_sell(
                        order_item.units)
                else:
                    logging.info(f'[APP][COMMAND] 시나리오에 판매 요청을 보내는 중입니다.')
                    order_id = self._scenario.trade_market_sell(
                        order_item.units)

                self.balance.add(tools.get_krw(order_item.units, bid))
                self.balance.sub_units(order_item.units)
                order_item.ongoing(order_id=order_id, bid=bid)

            else:
                raise ValueError(f'invalid command {command}')

        return command

print("""
██╗  ██╗ █████╗ ███╗   ██╗ ██████╗  █████╗ ███╗   ██╗ ██████╗ 
██║  ██║██╔══██╗████╗  ██║██╔════╝ ██╔══██╗████╗  ██║██╔════╝ 
███████║███████║██╔██╗ ██║██║  ███╗███████║██╔██╗ ██║██║  ███╗
██╔══██║██╔══██║██║╚██╗██║██║   ██║██╔══██║██║╚██╗██║██║   ██║
██║  ██║██║  ██║██║ ╚████║╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ 

**Examples**
1. python3 -m hangang --model cmo_v1 --balance 1000000 --scenario-name 1h-bithumb-backtest --test --order-currency LUNA --wait-seconds 0.001 --period 4 --scenario-price-type avg_price

2. python3 -m hangang --model cmo --balance 1000000 --scenario-name 1m-bithumb-backtest --test --order-currency LUNA --wait-seconds 0.001 --period 3

3. python3 -m hangang --model wave --balance 1000000 --scenario-name 3m-bithumb-backtest --test --debug --order-currency BTC --wait-seconds 1

# 실시간 테스트
4. python3 -m hangang --model wave --balance 1500 --order-currency EOS --wait-seconds 1 --scenario-name realtime --test

5. python3 -m hangang --model cmo --balance 1500 --order-currency EOS --wait-seconds 10 --period 4 --test

6. [PROD] python3 -m hangang --model wave --balance 1500 --order-currency EOS --wait-seconds 10


""")
parser = argparse.ArgumentParser(description='')
parser.add_argument('--model', help='model name', required=True)
parser.add_argument('--balance', help='balance', required=True, type=int)
parser.add_argument('--scenario-name', help='scenario name',
                    required=False, default='')
parser.add_argument('--test', action='store_true')
parser.add_argument('--debug', action='store_true')
parser.add_argument('--order-currency', help='주문 통화(코인)', required=True)
parser.add_argument('--wait-seconds', help='대기 시간', default=60, type=float)
parser.add_argument('--scenario-price-type', help='시나리오에서 사용하는 가격 타입 - end_price | avg_price | ...', default='end_price')
parser.add_argument('--period', help='CMO 모델에서 사용하는 매개변수', default=6, type=int)
parser.add_argument('--commission-rate', help='거래소 수수료 비율', default=0.25, type=float)

args = parser.parse_args()


print(args)

if args.debug:
    logging._logger.setLevel(level=logging.logging.DEBUG)

Hangang(args).main()
