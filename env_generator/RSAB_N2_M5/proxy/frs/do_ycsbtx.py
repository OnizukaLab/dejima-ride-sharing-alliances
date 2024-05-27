import dejimautils
from transaction import Tx
import config
import ycsbutils
import json
import sqlparse

def doYCSB_frs():
    # create new tx
    global_xid = dejimautils.get_unique_id()
    tx = Tx(global_xid)
    config.tx_dict[global_xid] = tx

    # workload
    stmts = ycsbutils.get_workload_for_ycsb(5, 5)

    # get local locks and get lineages
    lock_stmts_for_read = []
    get_lineage_stmts = []
    for stmt in stmts:
        if stmt.startswith("SELECT"):
            lock_stmts_for_read.append(stmt + " FOR SHARE NOWAIT")
        elif stmt.startswith("UPDATE"):
            where_clause = sqlparse.parse(stmt)[0][-1].value
            get_lineage_stmts.append("SELECT lineage FROM bt {} FOR UPDATE NOWAIT".format(where_clause))
    try:
        miss_flag = True
        lineages = []
        for stmt in lock_stmts_for_read:
            tx.cur.execute(stmt)
            if tx.cur.fetchone() != None:
                miss_flag = False
        for stmt in get_lineage_stmts:
            tx.cur.execute(stmt)
            try:
                lineage, *_ = tx.cur.fetchone()
                lineages.append(lineage)
            except:
                continue
        if lineages != []:
            miss_flag = False
    except:
        # abort during local lock
        tx.abort()
        del config.tx_dict[global_xid]
        return False

    if miss_flag:
        tx.abort()
        del config.tx_dict[global_xid]
        return "miss"

    # lock request
    if not lineages == []:
        result = dejimautils.lock_request(lineages, global_xid)
    else:
        result = "Ack"

    if result != "Ack":
        # abort during global lock, release lock
        dejimautils.release_lock_request(global_xid) 
        tx.abort()
        del config.tx_dict[global_xid]
        return False

    # execution
    try:
        for stmt in stmts:
            tx.cur.execute(stmt)
    except:
        # abort during local execution
        dejimautils.release_lock_request(global_xid) 
        tx.abort()
        del config.tx_dict[global_xid]
        return False

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
        return False
    
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

    return commit
