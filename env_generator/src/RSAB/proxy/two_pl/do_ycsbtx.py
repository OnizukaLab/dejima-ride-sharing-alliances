import dejimautils
from transaction import Tx
import config
import ycsbutils
import json
import sqlparse

def doYCSB_2pl():
    # create new tx
    global_xid = dejimautils.get_unique_id()
    tx = Tx(global_xid)
    config.tx_dict[global_xid] = tx

    # workload
    stmts = ycsbutils.get_workload_for_ycsb(5, 5)

    lock_stmts = []
    for stmt in stmts:
        if stmt.startswith("SELECT"):
            lock_stmts.append(stmt + " FOR SHARE NOWAIT")
        elif stmt.startswith("UPDATE"):
            where_clause = sqlparse.parse(stmt)[0][-1].value
            lock_stmts.append("SELECT * FROM bt {} FOR UPDATE NOWAIT".format(where_clause))
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
        return "miss"

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
        return False
    
    if prop_dict != {}:
        result = dejimautils.prop_request(prop_dict, global_xid, "2pl")
    else:
        result = "Ack"

    if result != "Ack":
        commit = False
    else:
        commit = True

    # termination
    if commit:
        tx.commit()
        dejimautils.termination_request("commit", global_xid, "2pl")
    else:
        tx.abort()
        dejimautils.termination_request("abort", global_xid, "2pl")
    del config.tx_dict[global_xid]

    return commit
