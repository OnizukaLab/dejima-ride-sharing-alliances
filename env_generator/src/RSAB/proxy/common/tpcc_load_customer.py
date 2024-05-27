import json
import dejimautils
import tpccutils
import config
from transaction import Tx

class TPCCLoadCustomer(object):
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

        # load
        print("load start")

        # create new tx
        global_xid = dejimautils.get_unique_id()
        tx = Tx(global_xid)
        config.tx_dict[global_xid] = tx

        # lock all dbs
        result = dejimautils.lock_request(['dummy'], global_xid)

        # execution
        try:
            w_id = (int(config.peer_name.strip("Peer")) - 1) // 10 + 1
            d_id = (int(config.peer_name.strip("Peer")) - 1) % 10 + 1
            c_stmt, h_stmt = tpccutils.get_loadstmt_for_customer_history(w_id, d_id)
            tx.cur.execute(c_stmt)
            tx.cur.execute(h_stmt)
            o_stmt, ol_stmt, no_stmt = tpccutils.get_loadstmt_for_orders_neworders_orderline(w_id, d_id)
            tx.cur.execute(o_stmt)
            tx.cur.execute(ol_stmt)
            tx.cur.execute(no_stmt)
        except Exception as e:
            # abort during local execution
            print(e)
            dejimautils.release_lock_request(global_xid) 
            tx.abort()
            del config.tx_dict[global_xid]
            resp.text = "local execution error"
            return

        # propagation
        try:
            tx.cur.execute("SELECT txid_current()")
            local_xid, *_ = tx.cur.fetchone()
            prop_dict = {}
            for dt in config.dt_list:
                target_peers = list(config.dejima_config_dict['dejima_table'][dt])
                target_peers.remove(config.peer_name)
                if target_peers == []: continue

                for bt in config.bt_list:
                    tx.cur.execute("SELECT {}_propagate_updates_to_{}()".format(bt, dt))
                tx.cur.execute("SELECT public.{}_get_detected_update_data({})".format(dt, local_xid))
                delta, *_ = tx.cur.fetchone()

                if delta == None: continue
                delta = json.loads(delta)

                prop_dict[dt] = {}
                prop_dict[dt]['peers'] = target_peers
                prop_dict[dt]['delta'] = delta

                tx.extend_childs(target_peers)

        except Exception as e:
            # abort during getting BIRDS result
            print('error during BIRDS: ', e)
            dejimautils.release_lock_request(global_xid) 
            tx.abort()
            del config.tx_dict[global_xid]
            resp.text = "BIRDS execution error"
            return
        
        if prop_dict != {}:
            result = dejimautils.prop_request(prop_dict, global_xid, "frs")
        else:
            result = "Ack"

        if result != "Ack":
            commit = False
        else:
            commit = True

        # termination
        if commit:
            tx.commit()
            dejimautils.termination_request("commit", global_xid, "frs")
        else:
            tx.abort()
            dejimautils.termination_request("abort", global_xid, "frs")
        del config.tx_dict[global_xid]

        if commit:
            msg = "success"
            print("success")
        else:
            msg = "prop error"
        resp.text = msg
        return
