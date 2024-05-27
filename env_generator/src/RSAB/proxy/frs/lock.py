import json
import config
import time
from transaction import Tx

class Lock(object):
    def __init__(self):
        pass

    def on_post(self, req, resp):
        time.sleep(config.SLEEP_MS * 0.001)

        if req.content_length:
            body = req.bounded_stream.read()
            params = json.loads(body)

        global_xid = params['xid']
        tx = Tx(global_xid)
        config.tx_dict[global_xid] = tx

        # lock with lineages
        bt_list = config.dejima_config_dict['base_table'][config.peer_name]
        # hardcode (lineage name)
        for bt in bt_list:
            if bt == "customer":
                lineage_col_name = "c_lineage"
            else:
                lineage_col_name = "lineage"
            stmt = "SELECT {} FROM {} WHERE ".format(lineage_col_name, bt) + " OR ".join(["{} = '{}'".format(lineage_col_name, lineage) for lineage in params['lineages']]) + " FOR UPDATE NOWAIT"

        try:
            tx.cur.execute(stmt)
            result = tx.cur.fetchone()
            if result == None:
                tx.abort()
                del config.tx_dict[global_xid]
        except Exception as e:
            # print("DB ERROR: ", e)
            resp.text = json.dumps({"result": "Nak"})
            return
        
        resp.text = json.dumps({"result": "Ack"})
        return
