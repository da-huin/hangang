# Hangang

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Contributing](../CONTRIBUTING.md)

## About <a name = "about"></a>

가상화폐 자동매매 프로그램입니다.

## Getting Started <a name = "getting_started"></a>

### Prerequisites

```
1. docker 설치
2. docker-compose.yaml 파일에서 aws credential 경로 수정
```

### Installing

```
1. bash build.sh
2. bash compose.sh
3. docker exec -it hangang bash
4. cd /app
5. python3 app.py -h
```

### 모델 추가하는 방법
1. models 폴더에서 `template_model.py` 파일을 복제합니다.
2. `{모델명}_model.py`로 파일 이름을 변경합니다.
3. `__init__()` 함수는 아래의 매개변수를 입력받습니다.
    * `order_currency`: 가상화폐 단위입니다. 예) BTC
    * `test`: 테스트 여부입니다. `--test`를 입력했다면 이 값이 `True`가 됩니다.
4. `update()` 함수는 아래의 매개변수를 입력받습니다.
    * `kind`: 데이터 종류입니다. 현재는 orderbook만 들어옵니다.
    * `data`: kind가 orderbook 이라면 아래의 데이터가 들어옵니다.
        * `ask`: 판매자가 원하는 가격
        * `bid`: 구매자가 원하는 가격
        * `data`: API로 받은 데이터 원본
5. `event()` 함수는 아래의 매개변수를 입력받습니다.
    * `kind`: 이벤트 종류입니다.
        * `transaction` data:
            * kind가 buy인 경우:
                ```json
                "kind": "buy",
                "order_id": "거래소에 요청한 후 받은 주문번호",
                "units": "수량",
                "price": "구매 요청 가격",
                "message": "모델에서 구매 요청시에 보낸 메세지"
                ```
            * kind가 sell인 경우:
                ```json
                "kind": "sell",
                "order_id": "거래소에 요청한 후 받은 주문번호",
                "units": "수량",
                "price": "판매 요청 가격",
                "ask": "요청 당시의 ask",
                "message": "모델에서 판매 요청시에 보낸 메세지"
                ```
        * `command_failed` data:
            * `code`:
                * `-1`: 구매 최소값인 1000원을 초과하지 않아서 구매에 실패함
6. 모델에서 구매, 판매 요청을 보내려면 `update()`함수에서 `list` 타입으로 명령어들을 반환하면 됩니다.
    * 구매 요청
        ```python
        command = {
            'kind': 'buy',
            'rate': '가지고 있는 돈에서 투자할 비율',
            'message': '메세지'
        }
        ```
    * 판매 요청
        ```python
        command = {
            'kind': 'sell',
            'units': '수량',
            'message': '메세지'
        }
        ```


### Temporary TODO

1. 리팩토링
 - 구매, 판매 commands -> 클래스로 바꾸고 command.buy() 와 같은 형식으로 한 줄로 표현이 되도록 한다.
 - app.py import 경로 경고 확인