import requests
from simple_utils import simple_logging as logging
import uuid
from collections import OrderedDict


class PointType():
    INITALIZATiON = 0
    TRANSACTION_BUY = 1


class Point():
    def __init__(self, kind, ask=-1, bid=-1, price=-1, units=-1, additional_bought=False):
        self.kind = kind
        self.bid = bid
        self.ask = ask
        self.price = price
        self.units = units
        self.additional_bought = additional_bought
        self.point_id = uuid.uuid1()
        self._status = 'on'

    def on(self):
        self._status = 'on'

    def off(self):
        self._status = 'off'

    def is_on(self):
        return self._status == 'on'


class Line():
    def __init__(self):
        self._points = OrderedDict()
        self._history = list()

    @property
    def points(self):
        return self._points

    def insert(self, x: Point):
        self.valid_check(x)
        self._points[x.point_id] = x
        self._history.append({
            'method': 'insert',
            'point': x
        })

    def delete(self, x: Point):
        self.valid_check(x)
        del self._points[x.point_id]

        self._history.append({
            'method': 'delete',
            'point': x
        })

    def valid_check(self, x: Point):
        if not isinstance(x, Point):
            raise ValueError('Point 클래스 인스턴스만 입력할 수 있습니다.')


class ModelProperty():
    rotation = {
        'initialization': {
            'buy_rate': 0.97,
            'command_buy_balance_rate': 0.30
        },

        'buy': {
            'sell_rate': 1.03,
            'additional_buy_rate': 0.92,
            'additional_buy_balance_rate': 0.15
        }
    }


class WaveModel():
    def __init__(self, order_currency):
        """
        - Line 구조체 안에 Point라는 인스턴스가 있다.
        - Point 인스턴스는 모델이 새로운 데이터를 받았을 때, 데이터를 확인하고 타입에 따라 그에 맞는 행동을 한다.
        - rotation 함수에서 Line 구조체를 순환하면서 Point를 확인한다.

        Rule
        - 가장 처음에 Point 인스턴스를 생성하는데 kind는 initalization 으로 하고 구매할 수 있는 가격(bid)을 입력한다.
            - 새로운 데이터가 들어왔을 때 property의 initalization.buy_rate 만큼의 가격이 되면 
                initalization.command_buy_balance_rate 만큼 구매 명령을 보낸다.
        - 구매가 완료되면 Point를 생성하는데 kind는 buy로 하고 구매 가격을 price에 넣고 수량을 넣는다.
            - 구매 가격 x 수량으로 KRW를 구할 수 있다.
            - Point가 buy인 것은 두 가지 규칙을 따른다.
                1. property의 구매 가격을 기준으로 buy.sell_rate 만큼의 가격이 되었을 때 판매한다.
                2. property의 구매 가격을 기준으로 buy.additional_buy_rate 만큼의 가격이 되었을 때 
                    buy.additional_buy_balance_rate 만큼 추가구매한다. 이후에는 더이상 추가구매하지 않는다.
            - 위의 경우 Point가 여러개가 될 수 있는 경우는 두번째이다.                 
        """
        self._line = Line()
        self._initalized = False
        self._order_currency = order_currency

    @property
    def line(self):
        return self._line

    def update(self, kind, data):

        logging.info(f'[WAVEMODEL UPDATE] 라인 길이: {len(self.line.points)}')
        commands = self.rotation(kind, data)
        if kind == 'orderbook':
            ask = data['ask']
            bid = data['bid']

            if not self._initalized:

                self.line.insert(Point(kind=PointType.INITALIZATiON, ask=ask))
                self._initalized = True
                logging.info(
                    '[WAVEMODEL UPDATE] 추가된 포인트: INITALIZATiON')
        else:
            raise ValueError(f'invalid kind {kind}')

        return commands

    def event(self, kind, data):

        logging.info(f'[WAVEMODEL EVENT] 타입: {kind}')
        logging.info(f'[WAVEMODEL EVENT] 데이터: {data}')

        if kind == 'transaction':
            if data['order']['kind'] == 'buy':
                self.line.insert(Point(
                    kind=PointType.TRANSACTION_BUY, price=data['order']['price'], units=data['order']['units'], additional_bought=False))

            elif data['order']['kind'] == 'sell':
                self.line.insert(Point(kind=PointType.INITALIZATiON, ask=data['order']['ask']))
            else:
                pass
        elif kind == 'command_fail':
            command_kind = data['command_kind']
            code = data['code']
            if command_kind == 'buy' and code == -1:
                pass
            else:
                pass

        else:
            raise ValueError(f'invalid kind {kind}')

    def rotation(self, kind, data):
        if kind == 'orderbook':
            bid = data['bid']
            ask = data['ask']
            logging.info(f'[WAVEMODEL ROTATION] ask: {ask}, bid: {bid}')
            commands = []
            logging.info(f'[WAVEMODEL ROTATION] Line rotation start')
            for key, point in self.line.points.items():
                if not point.is_on():
                    continue

                logging.info(f'[WAVEMODEL ROTATION] kind: {point.kind}')
                if point.kind == PointType.INITALIZATiON:
                    buy_target = int(point.ask * \
                        ModelProperty.rotation['initialization']['buy_rate'])
                    if ask > buy_target:
                        logging.info(
                            f'[WAVEMODEL ROTATION][{point.kind}] ask({ask})가 아직 구매 목표({buy_target})까지의 가격이 되지 않았습니다.')
                        continue
                    balance_rate = ModelProperty.rotation['initialization']['command_buy_balance_rate']
                    command = {
                        'kind': 'buy',
                        'rate': balance_rate,
                        'ask': ask
                    }
                    commands.append(command)
                    point.off()

                    logging.info(
                        f'[WAVEMODEL ROTATION][{point.kind}] 명령어 목록에 balance_rate({balance_rate}) 만큼 구매를 요청했습니다.')

                elif point.kind == PointType.TRANSACTION_BUY:

                    sell_target = int(point.price *
                                ModelProperty.rotation['buy']['sell_rate'])
                    additional_buy_target = int(point.price *
                                            ModelProperty.rotation['buy']['additional_buy_rate'])
                    if bid > sell_target:
                        logging.info(
                            f'[WAVEMODEL ROTATION][{point.kind}] bid({bid})가 판매 목표({sell_target})에 도달했습니다.')
                        command = {
                            'kind': 'sell',
                            'units': point.units,
                            'bid': bid,
                            # 정보제공용 
                            'ask': ask

                        }
                        commands.append(command)

                        point.off()

                        logging.info(
                            f'[WAVEMODEL ROTATION][{point.kind}] 명령어 목록에 가지고 있던 {point.units} 만큼 판매를 요청했습니다.')

                    elif (ask < additional_buy_target) and not point.additional_bought:
                        logging.info(
                            f'[WAVEMODEL ROTATION][{point.kind}] ask({ask})가 추가 구매 목표({additional_buy_target})에 도달했습니다.')

                        additional_buy_balance_rate = ModelProperty.rotation[
                            'buy']['additional_buy_balance_rate']
                        command = {
                            'kind': 'buy',
                            'rate': additional_buy_balance_rate,
                            'ask': ask
                        }

                        commands.append(command)
                        point.additional_bought = True

                        point.off()
                        logging.info(
                            f'[WAVEMODEL ROTATION][{point.kind}] 명령어 목록에 {additional_buy_balance_rate} 만큼 구매를 요청했습니다.')
                    else:
                        logging.info(f'[WAVEMODEL ROTATION][{point.kind}] 판매 목표({bid}/{sell_target}) 또는 추가 구매 목표({ask}/{additional_buy_target}) 에 도달하지 않았기 때문에 아무 행동도 하지 않았습니다.')
                else:
                    raise ValueError(f'invalid kind {point.kind}')

            for off_point in [point for key, point in self.line.points.items() if not point.is_on()]:
                self.line.delete(off_point)
        else:
            raise ValueError(f'invalid kind {kind}')

        return commands
