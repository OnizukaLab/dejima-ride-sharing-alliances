import json
import dejimautils
import ycsbutils
import config
from transaction import Tx

class YCSBLoad(object):
    def __init__(self):
        pass

    def on_get(self, req, resp):
        # get params
        params = req.params
        param_keys = ["start_id", "record_num", "step"]
        for key in param_keys:
            if not key in params.keys():
                msg = "Invalid parameters"
                resp.text = msg
                return

        start_id = int(params['start_id'])
        record_num = int(params['record_num'])
        step = int(params['step'])
            
        # load
        print("load start")

        # create new tx
        global_xid = dejimautils.get_unique_id()
        tx = Tx(global_xid)
        config.tx_dict[global_xid] = tx

        # workload
        stmt = ycsbutils.get_stmt_for_load(start_id, record_num, step)

        # lock all dbs
        result = dejimautils.lock_request(['dummy'], global_xid)

        # execution
        try:
            tx.cur.execute(stmt)
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
