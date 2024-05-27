import json
import config
import time

class Unlock(object):
    def __init__(self):
        pass

    def on_post(self, req, resp):
        time.sleep(config.SLEEP_MS * 0.001)

        if req.content_length:
            body = req.bounded_stream.read()
            params = json.loads(body)

        global_xid = params['xid']
        src_peer = params['src_peer']

        if global_xid in config.tx_dict and config.peer_name != src_peer:
            tx = config.tx_dict[global_xid]
            tx.abort()
            if global_xid in config.parent_list:
                del config.parent_list[global_xid]
            del config.tx_dict[global_xid]

        resp.text = json.dumps({"result": "Ack"})
        return