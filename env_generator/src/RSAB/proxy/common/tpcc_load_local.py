import dejimautils
import tpccutils
import config
from transaction import Tx

class TPCCLoadLocal(object):
    def __init__(self):
        pass

    def on_get(self, req, resp):
        params = req.params
        param_keys = ["peer_num"]
        for key in param_keys:
            if not key in params.keys():
                msg = "Invalid parameters"
                resp.text = msg
                return

        peer_num = int(params['peer_num'])
        if peer_num % 10 != 0:
            warehouse_num = peer_num // 10 + 1
        else:
            warehouse_num = int(peer_num / 10)
        config.warehouse_num = warehouse_num

        # load
        print("load start")

        # create new tx
        global_xid = dejimautils.get_unique_id()
        tx = Tx(global_xid)
        config.tx_dict[global_xid] = tx

        # execution
        try:
            for w_id in range(1, warehouse_num+1):
                tx.cur.execute(tpccutils.get_loadstmt_for_warehouse(w_id))
            tx.cur.execute(tpccutils.get_loadstmt_for_item())
            for w_id in range(1, warehouse_num+1):
                for i in [1, 20001, 40001, 60001, 80001]:
                    tx.cur.execute(tpccutils.get_loadstmt_for_stock(w_id, i))
            for w_id in range(1, warehouse_num+1):
                tx.cur.execute(tpccutils.get_loadstmt_for_district(w_id))
        except Exception as e:
            # abort during local execution
            print(e)
            tx.abort()
            del config.tx_dict[global_xid]
            resp.text = "local execution error"
            return

        # termination
        tx.commit()
        del config.tx_dict[global_xid]

        resp.text = "success"
        return
