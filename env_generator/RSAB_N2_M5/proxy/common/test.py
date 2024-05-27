import json
import config
from pool import pool

class Test(object):
    def __init__(self):
        pass

    def on_post(self, req, resp):
        if req.content_length:
            body = req.bounded_stream.read()
            params = json.loads(body)

        msg = {"result": "Ack"}
        resp.text = "true"
        return
    
    def on_get(self, req, resp):
        resp.text = "Ack"
        params = req.params

        print("Ongoing Tx's ID: ", list(config.tx_dict.keys()))
        print("# Used connection: ", len(pool._used.keys()))
        return