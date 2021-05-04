# import aws_glove
# from exchange.bithumb import bithumb
# class Transactions():
#     def __init__(self, bucket_name, order_currency):
#         self._s3_client = aws_glove.client('s3', bucket_name=bucket_name)
#         self._order_currency = order_currency
#         self._data = self._load()
        

#     def _load(self):
#         try:
#             return self._s3_client.load(self._get_path())
#         except:
#             return []
    
#     def update(self):
#         pass

#     def append(self):
#         bithumb.user_transactions(len(self._data), self._order_currency)
#         self._s3_client.save(self._get_path())

#     def _get_path(self):
#         return f'/hangang/bithumb/transactions/{self._order_currency}.parquet'
    
#         # bithumb.user_transactions(offset, order_currency)
