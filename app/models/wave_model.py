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
    def __init__(self, test):
        if test:
            self.rotation = {
                'initialization': {
                    'buy_rate': 1,
                    'command_buy_balance_rate': 0.70
                },
                'buy': {
                    'sell_rate': 1.03,
                    'additional_buy_rate': 0.92,
                    'additional_buy_balance_rate': 0.50,
                    'loss_cut_rate': 0.70
                }
            }
        else:
            self.rotation = {
                'initialization': {
                    'buy_rate': 0.97,
                    'command_buy_balance_rate': 0.30
                },
                'buy': {
                    'sell_rate': 1.03,
                    'additional_buy_rate': 0.92,
                    'additional_buy_balance_rate': 0.15
                },
            }

# [INFO][2021-05-05 19:18:00] [APP][ORDERS] 잔고: Balance: 143744, Units: 199.30799999999988
# [INFO][2021-05-05 19:18:00] [APP][ORDERS] events: {'order_id': '2b6e4aaa-ad8b-11eb-ad60-0242ac130002', 'units': 44.161, 'kind': 'sell', 'bid': 1637.5, 'ask': 1657.5, 'message': 'sell'}
class WaveModel():
    def __init__(self, order_currency, test):
        self._line = Line()
        self._initalized = False
        self._order_currency = order_currency
        self._property = ModelProperty(test)

    @property
    def line(self):
        return self._line

    def update(self, kind, data):

        logging.debug(f'[WAVEMODEL UPDATE] 라인 길이: {len(self.line.points)}')
        commands = self.rotation(kind, data)
        if kind == 'orderbook':
            ask = data['ask']
            bid = data['bid']

            if not self._initalized:

                self.line.insert(Point(kind=PointType.INITALIZATiON, ask=ask))
                self._initalized = True
                logging.debug(
                    '[WAVEMODEL UPDATE] 추가된 포인트: INITALIZATiON')
        else:
            raise ValueError(f'invalid kind {kind}')

        return commands

    def event(self, kind, data):

        logging.debug(f'[WAVEMODEL EVENT] 타입: {kind}')
        logging.debug(f'[WAVEMODEL EVENT] 데이터: {data}')

        if kind == 'transaction':
            if data['order']['kind'] == 'buy':
                self.line.insert(Point(
                    kind=PointType.TRANSACTION_BUY, price=data['order']['price'], units=data['order']['units'], additional_bought=False))

            elif data['order']['kind'] == 'sell':
                if len(self._line.points) == 0:
                    self.line.insert(Point(kind=PointType.INITALIZATiON, ask=data['order']['price']))
            else:
                pass
        elif kind == 'command_failed':
            code = data['code']
            if code == -1:
                pass
            else:
                pass

        else:
            raise ValueError(f'invalid kind {kind}')

    def rotation(self, kind, data):
        if kind == 'orderbook':
            bid = data['bid']
            ask = data['ask']
            
            logging.debug(f'[WAVEMODEL ROTATION] ask: {ask}, bid: {bid}')
            commands = []
            logging.debug(f'[WAVEMODEL ROTATION] Line rotation start')
            for key, point in self.line.points.items():
                if not point.is_on():
                    continue

                logging.debug(f'[WAVEMODEL ROTATION] kind: {point.kind}')
                if point.kind == PointType.INITALIZATiON:

                    # buy_target = int(point.ask * \
                    #     self._property.rotation['initialization']['buy_rate'])
                    # if ask > buy_target:
                    #     logging.info(
                    #         f'[WAVEMODEL ROTATION][{point.kind}] ask({ask})가 아직 구매 목표({buy_target})까지의 가격이 되지 않았습니다.')
                    #     continue
                    balance_rate = self._property.rotation['initialization']['command_buy_balance_rate']
                    command = {
                        'kind': 'buy',
                        'rate': balance_rate,
                        # 'ask': ask,
                        'message': 'buy'
                    }
                    commands.append(command)
                    point.off()

                    logging.debug(
                        f'[WAVEMODEL ROTATION][{point.kind}] 명령어 목록에 balance_rate({balance_rate}) 만큼 구매를 요청했습니다.')

                elif point.kind == PointType.TRANSACTION_BUY:

                    sell_target = int(point.price *
                                self._property.rotation['buy']['sell_rate'])
                    additional_buy_target = int(point.price *
                                            self._property.rotation['buy']['additional_buy_rate'])

                    loss_cut_target = int(point.price * self._property.rotation['buy']['loss_cut_rate'])
                    if bid > sell_target:
                        logging.debug(
                            f'[WAVEMODEL ROTATION][{point.kind}] bid({bid})가 판매 목표({sell_target})에 도달했습니다.')
                        command = {
                            'kind': 'sell',
                            'units': point.units,
                            # 'bid': bid,
                            # # 정보제공용 
                            # 'ask': ask,
                            'message': 'sell'
                        }
                        commands.append(command)

                        point.off()

                        logging.debug(
                            f'[WAVEMODEL ROTATION][{point.kind}] 명령어 목록에 가지고 있던 {point.units} 만큼 판매를 요청했습니다.')

                    elif (ask < additional_buy_target) and not point.additional_bought:
                        logging.debug(
                            f'[WAVEMODEL ROTATION][{point.kind}] ask({ask})가 추가 구매 목표({additional_buy_target})에 도달했습니다.')

                        additional_buy_balance_rate = self._property.rotation[
                            'buy']['additional_buy_balance_rate']
                        command = {
                            'kind': 'buy',
                            'rate': additional_buy_balance_rate,
                            'ask': ask,
                            'message': 'additional_buy'

                        }

                        commands.append(command)
                        point.additional_bought = True

                        # point.off()
                        logging.debug(
                            f'[WAVEMODEL ROTATION][{point.kind}] 명령어 목록에 {additional_buy_balance_rate} 만큼 구매를 요청했습니다.')
                    elif (ask < loss_cut_target):
                        logging.debug(
                            f'[WAVEMODEL ROTATION][{point.kind}] bid({bid})가 손절 목표({loss_cut_target})에 도달했습니다.')                        
                        command = {
                            'kind': 'sell',
                            'units': point.units,
                            'bid': bid,
                            # 정보제공용 
                            'ask': ask,
                            'message': 'loss cut'

                        }
                        commands.append(command)
                        point.off()
                    
                    else:
                        logging.debug(f'[WAVEMODEL ROTATION][{point.kind}] 판매 목표({bid}/{sell_target}) 또는 추가 구매 목표({ask}/{additional_buy_target}) 또는 손절 목표({bid}/{loss_cut_target}) 에 도달하지 않았기 때문에 아무 행동도 하지 않았습니다.')
                else:
                    raise ValueError(f'invalid kind {point.kind}')

            for off_point in [point for key, point in self.line.points.items() if not point.is_on()]:
                self.line.delete(off_point)
        else:
            raise ValueError(f'invalid kind {kind}')

        return commands
