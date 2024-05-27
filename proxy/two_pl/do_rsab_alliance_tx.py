import dejimautils
from transaction import Tx
import config
import rsabutils
import json
import sqlparse
import time
import numpy as np

def doRSAB_ALLIANCE_2pl():
    LOCK_DEBUG = False
    measure_time = True
    timestamps = []
    timestamp = []
    start_time = time.perf_counter()
    timestamp.append(start_time)
    
    config.result_measurement.start_tx()
    
    # create new tx
    global_xid = dejimautils.get_unique_id()
    tx = Tx(global_xid)
    config.tx_dict[global_xid] = tx
    
    # workload
    stmts = rsabutils.get_workload_for_alliance()
    if stmts == []:
        tx.abort()
        del config.tx_dict[global_xid]
        return "miss"

    lock_stmts = []
    for stmt in stmts:
        if stmt.startswith("SELECT"):
            lock_stmts.append(stmt + " FOR SHARE NOWAIT")
        elif stmt.startswith("UPDATE"):
            where_clause = sqlparse.parse(stmt)[0][-1].value
            lock_stmts.append("SELECT * FROM mt {} FOR UPDATE NOWAIT".format(where_clause))
    try:
        miss_flag = True
        # lock
        timestamp.append(time.perf_counter())
        for stmt in lock_stmts:
            tx.cur.execute(stmt)            
            if tx.cur.fetchone() != None:
                miss_flag = False 
        # execution
        timestamp.append(time.perf_counter())
        for stmt in stmts:
            tx.cur.execute(stmt)
    except:
        # abort during local lock
        if LOCK_DEBUG: print("local lock failed")
        tx.abort()
        del config.tx_dict[global_xid]
        config.timestamp_management.commit_or_abort(start_time, time.perf_counter(), "abort_in_local")
        config.result_measurement.abort_tx('local')
        return False

    if miss_flag:
        tx.abort()
        del config.tx_dict[global_xid]
        return "miss"
    
    if LOCK_DEBUG: print("succeeded")
    
    timestamp.append(time.perf_counter())
    # propagation
    try:
        tx.cur.execute("SELECT txid_current()")
        local_xid, *_ = tx.cur.fetchone()
        timestamp.append(time.perf_counter())
        
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
        config.timestamp_management.commit_or_abort(start_time, time.perf_counter(), "abort_from_BIRDS")
        return False
    
    timestamp.append(time.perf_counter())
    if prop_dict != {}:
        result = dejimautils.prop_request(prop_dict, global_xid, "2pl", measure_time=measure_time)
    else:
        result = "Ack"
    timestamp.append(time.perf_counter())
    
    if result == "Ack" and measure_time == True:
        result = []
    if isinstance(result, list):
        timestamps = result
        timestamps.append(timestamp)
        timestamps = ((np.array(timestamps)-start_time)*1000).tolist()
        # print(timestamps)
        config.timestamp_management.add_timestamps(timestamps)
        result = "Ack"
    
    if result != "Ack":
        commit = False
    else:
        commit = True
    
    # termination
    if commit:
        if LOCK_DEBUG: print("released")
        tx.commit()
        dejimautils.termination_request("commit", global_xid, "2pl")
        config.timestamp_management.commit_or_abort(start_time, time.perf_counter(), "commit")
        
        all_select = True
        for stmt in stmts:
            if not stmt.startswith("SELECT"): all_select = False
        if all_select: config.result_measurement.commit_tx('read')
        else: config.result_measurement.commit_tx('update')
            
        config.stmts = []
    else:
        if LOCK_DEBUG: print("abort")
        tx.abort()
        dejimautils.termination_request("abort", global_xid, "2pl")
        config.timestamp_management.commit_or_abort(start_time, time.perf_counter(), "abort_during_prop")
        config.result_measurement.abort_tx('global')
    del config.tx_dict[global_xid]
    
    return commit
