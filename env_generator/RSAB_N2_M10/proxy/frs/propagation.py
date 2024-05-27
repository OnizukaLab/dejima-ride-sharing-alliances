import json
import dejimautils
import config
import time
from transaction import Tx

class FRSPropagation(object):
    def __init__(self):
        pass

    def on_post(self, req, resp):
        DATA_DEBUG = False
        timestamps = []
        timestamp = []
        timestamp.append(time.perf_counter())
        
        time.sleep(config.SLEEP_MS * 0.001)

        if req.content_length:
            body = req.bounded_stream.read()
            params = json.loads(body)
        
        if DATA_DEBUG: print("before lock ({})".format(params['xid']))
        
        # config.lock.acquire()
        start_lock_time = time.perf_counter()
        with config.propagation_lock:
            # start_lock_time = time.perf_counter()
            
            global_xid = params['xid']
            measure_time = params['measure_time']
            if global_xid in config.tx_dict:
                tx = config.tx_dict[global_xid]
                locked_flag = True
            else:
                tx = Tx(global_xid)
                config.tx_dict[global_xid] = tx
                locked_flag = False
                
            if measure_time: config.time_measurement.start_timer("acquire program lock", global_xid, start_lock_time)
            if measure_time: config.time_measurement.stop_timer("acquire program lock", global_xid)
            if measure_time: config.time_measurement.start_timer("in program lock", global_xid)
                
            # if tx.propagation_cnt > 0 and config.peer_name[:9] != "alliance0":
            #     resp.text = json.dumps({"result": "Ack"})
            #     # print("A propagation loop detected")
            #     return
            if tx.propagation_cnt == 0:
                tx.propagation_cnt += 1
            
            # update dejima table and propagate to base tables
            try:
                stmt = dejimautils.convert_to_sql_from_json(params['delta'])
                # additional lock for peers out of lock scope
                if not locked_flag:
                    for bt in config.bt_list:
                        # if bt == "customer":
                        #     for delete in params['delta']["deletions"]:
                        #         tx.cur.execute("SELECT * FROM customer WHERE c_w_id={} AND c_d_id={} AND c_id={} FOR UPDATE NOWAIT".format(delete['c_w_id'], delete['c_d_id'], delete['c_id']))
                        # elif bt == "mt":
                        #     for delete in params['delta']["deletions"]:
                        #         tx.cur.execute("SELECT * FROM mt WHERE id={} FOR UPDATE NOWAIT".format(delete['id']))
                        # else:
                        #     for delete in params['delta']["deletions"]:
                        #         tx.cur.execute("SELECT * FROM bt WHERE id={} FOR UPDATE NOWAIT".format(delete['id']))
                        timestamp.append(time.perf_counter())
                        if bt == "bt":
                            for delete in params['delta']["deletions"]:
                                tx.cur.execute("SELECT * FROM bt WHERE v={} FOR UPDATE NOWAIT".format(delete['v']))
                                # lock_stmts.append("SELECT * FROM bt WHERE v={} FOR UPDATE NOWAIT".format(delete['v']))
                        else:
                            for delete in params['delta']["deletions"]:
                                tx.cur.execute("SELECT * FROM mt WHERE v={} FOR UPDATE NOWAIT".format(delete['v']))
                                # lock_stmts.append("SELECT * FROM mt WHERE v={} FOR UPDATE NOWAIT".format(delete['v']))
                        timestamp.append(time.perf_counter())
                else:
                    timestamp.append(time.perf_counter())
                    timestamp.append(time.perf_counter())
                # print(stmt)
                tx.cur.execute(stmt)
                timestamp.append(time.perf_counter())
            except Exception as e:
                if measure_time: config.time_measurement.stop_timer("in program lock", global_xid, save=False)
                print("Error during prop lock and exec:", e)
                resp.text = json.dumps({"result": "Nak", "info": e.__class__.__name__})
                return
            
            # print("step1")
            
            try: 
                # get local xid
                tx.cur.execute("SELECT txid_current()")
                local_xid, *_ = tx.cur.fetchone()
                timestamp.append(time.perf_counter())
                
                # propagation
                updated_dt = params['delta']['view'].split('.')[1]
                tx.cur.execute("SELECT public.{}_get_detected_update_data({})".format(updated_dt, local_xid))
                if global_xid not in config.parent_list:
                    config.parent_list[global_xid] = [params['parent_peer']]
                else:
                    config.parent_list[global_xid].append(params['parent_peer'])
                prop_dict = {}
                for dt in config.dt_list:
                    if dt == updated_dt: continue
                    target_peers = list(config.dejima_config_dict['dejima_table'][dt])
                    target_peers.remove(config.peer_name)
                    # if params['parent_peer'] in target_peers: target_peers.remove(params["parent_peer"])
                    # for parent in config.parent_list[global_xid]:
                    #     if parent in target_peers: target_peers.remove(parent)
                    if target_peers == []: 
                        continue
                    
                    for bt in config.bt_list:
                        tx.cur.execute("SELECT {}_propagate_updates_to_{}()".format(bt, dt))
                    tx.cur.execute("SELECT public.{}_get_detected_update_data({})".format(dt, local_xid))
                    try:
                        delta, *_ = tx.cur.fetchone()
                    except: continue
                    
                    if delta == None: continue
                    delta = json.loads(delta)
                    # print(params['parent_peer'], target_peers, delta)

                    prop_dict[dt] = {}
                    prop_dict[dt]['peers'] = target_peers
                    prop_dict[dt]['delta'] = delta

                    tx.extend_childs(target_peers)

            except Exception as e:
                if measure_time: config.time_measurement.stop_timer("in program lock", global_xid, save=False)
                print("Error during getting prop data:", e)
                tx.reset_childs()
                msg = {"result": "Nak"}
                resp.text = json.dumps(msg)
                return
        
        if DATA_DEBUG: print("after lock ({})".format(global_xid))
        if DATA_DEBUG: print("{} {} {} \n\n".format(prop_dict, local_xid, global_xid), end="")
        if measure_time: config.time_measurement.stop_timer("in program lock", global_xid)
        # print(time.perf_counter()-start_lock_time)
        # config.lock.release()
        # print("step2")
        
        timestamp.append(time.perf_counter())
        if prop_dict != {} and config.peer_name != "alliance0":
            result = dejimautils.prop_request(prop_dict, global_xid, "frs", params['insert_delete'], measure_time)
        else:
            result = "Ack"
        timestamp.append(time.perf_counter())

        if result == "Ack" and measure_time == True:
            result = []
        if isinstance(result, list):
            timestamps = result
            timestamps.append(timestamp)
            result = "Ack"
        
        if result != "Ack":
            msg = {"result": "Nak"}
        else:
            msg = {"result": "Ack", "timestamps": timestamps}
            
        if result == "Ack" and params['insert_delete'] == True:
            dejimautils.update_candidate_list(params['delta'], params['parent_peer'])
        
        # print("step3")
        
        resp.text = json.dumps(msg)
        return