import json
import dejimautils
import rsabutils
import config
from transaction import Tx

class RSABLoadAlliance(object):
    def __init__(self):
        pass
    
    def get_updated_data(self, global_xid):
        tx = config.tx_dict[global_xid]
        uv_result = []
        try:
            # lock
            tx.cur.execute("SELECT * FROM uv FOR SHARE NOWAIT")
            uv_result = tx.cur.fetchall()
            if uv_result == None:
                return []
        except:
            # abort during local lock
            tx.abort()
            del config.tx_dict[global_xid]
            return False
        return uv_result
    
    def on_get(self, req, resp):
        # get params
        # params = req.params
        # param_keys = ["start_id", "record_num", "step"]
        # for key in param_keys:
        #     if not key in params.keys():
        #         msg = "Invalid parameters"
        #         resp.text = msg
        #         return
        
        # start_id = int(params['start_id'])
        # record_num = int(params['record_num'])
        # step = int(params['step'])
            
        # load
        print("load start")

        # create new tx
        global_xid = dejimautils.get_unique_id()
        tx = Tx(global_xid)
        config.tx_dict[global_xid] = tx

        # get updated data
        uv_result = self.get_updated_data(global_xid)
        if uv_result == False or uv_result == []:
            tx.abort()
            del config.tx_dict[global_xid]
            resp.text = "could not lock or found nothing to lock"
            return
        
        # workload
        lock_stmts = []
        stmts = []
        for updated_data in uv_result:
            lock_stmts.append("SELECT * FROM mt WHERE V={} FOR UPDATE NOWAIT".format(updated_data[0]))
            stmts.append("UPDATE mt SET U='false' WHERE V={}".format(updated_data[0]))
            config.candidate_record_id_list.append(updated_data[0])
        
        try:
            miss_flag = True
            # lock
            for stmt in lock_stmts:
                tx.cur.execute(stmt)            
                if tx.cur.fetchone() != None:
                    miss_flag = False 
            # execution
            for stmt in stmts:
                tx.cur.execute(stmt)
        except:
            # abort during local lock
            tx.abort()
            del config.tx_dict[global_xid]
            return False

        if miss_flag:
            tx.abort()
            del config.tx_dict[global_xid]
            resp.text = "miss"
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
