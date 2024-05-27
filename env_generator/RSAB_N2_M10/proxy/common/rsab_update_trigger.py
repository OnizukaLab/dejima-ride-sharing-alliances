import json
import dejimautils
import config
import time
from transaction import Tx

import psycopg2

class update(object):
    def __init__(self):
        pass

    def on_post(self, req, resp):
        time.sleep(config.SLEEP_MS * 0.001)

        if req.content_length:
            body = req.bounded_stream.read()
            params = json.loads(body)
        
        print(params)
        # stmt = dejimautils.convert_to_sql_from_json(params)
        # # stmt = "INSERT INTO a1 VALUES(5, 5, 5, 5)"
        # # stmt = "WITH updated1 AS (INSERT INTO a1 VALUES(5, 5, 5, 5) RETURNING true) SELECT * FROM updated1"
        # # stmt = "WITH updated1 AS (SELECT * FROM a1) SELECT * FROM updated1"
        # with self.connection:
        #     with self.connection.cursor() as cursor:
        #         cursor.execute(stmt)
        #         row = cursor.fetchall()
        #         print(row)
                
        #         cursor.execute("SELECT true")
        #         print(cursor.fetchall())
                
        # resp.text = "true"
        # print(json.dumps(params))
        return