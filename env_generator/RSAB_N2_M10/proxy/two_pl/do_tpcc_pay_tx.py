import dejimautils
from transaction import Tx
import config
import random
import tpccutils
import json
import math
from datetime import datetime

def doTPCC_PAY_2pl():
    # create new tx
    global_xid = dejimautils.get_unique_id()
    tx = Tx(global_xid)
    config.tx_dict[global_xid] = tx

    # prepare parameters
    w_id = random.randint(1, config.warehouse_num)
    d_id = random.randint(1, 10)
    if random.randint(1, 100) <= 85:
        c_d_id = d_id
        c_w_id = w_id
    else:
        c_d_id = random.randint(1, 10)
        c_w_id = random.randint(1, config.warehouse_num)
    if random.randint(1, 100) <= 40:
        c_id = tpccutils.nurand(1023, 1, 3000, tpccutils.C_FOR_C_ID)
        select_with_c_id_flag = True
    else:
        c_last = tpccutils.get_last(tpccutils.nurand(255,0,999,tpccutils.C_FOR_C_LAST))
        select_with_c_id_flag = False

    # h_amount is defined as string
    h_amount = '{:.2f}'.format(random.random() * 4999 + 1)
    h_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # get local locks, check whether miss or not, and get lineages
    try:
        miss_flag = True
        lineages = []

        tx.cur.execute("SELECT * FROM warehouse WHERE w_id = {} FOR UPDATE NOWAIT".format(w_id))

        tx.cur.execute("SELECT * FROM district WHERE d_w_id = {} AND d_id = {} FOR UPDATE NOWAIT".format(w_id, d_id))

        if select_with_c_id_flag:
            tx.cur.execute("SELECT c_lineage FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_id = {} FOR UPDATE NOWAIT".format(c_w_id, c_d_id, c_id))
            all_records = tx.cur.fetchall()
            if len(all_records) != 0:
                lineage, *_ = all_records[0]
                lineages.append(lineage)
                miss_flag = False
        else:
            tx.cur.execute("SELECT c_lineage FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_last = '{}' ORDER BY c_first FOR UPDATE NOWAIT".format(c_w_id, c_d_id, c_last))
            all_records = tx.cur.fetchall()
            if len(all_records) != 0:
                idx = math.ceil(len(all_records) / 2)
                lineage, *_ = all_records[idx-1]
                lineages.append(lineage)
                miss_flag = False
    except Exception as e:
        # abort during local lock
        tx.abort()
        del config.tx_dict[global_xid]
        return False

    if miss_flag:
        tx.abort()
        del config.tx_dict[global_xid]
        return "miss"

    # execution
    try:
        tx.cur.execute("SELECT w_name, w_street_1, w_street_2, w_city, w_state, w_zip FROM warehouse WHERE w_id = {} FOR UPDATE".format(w_id))
        w_name, w_street_1, w_street_2, w_city, w_state, w_zip = tx.cur.fetchone()

        tx.cur.execute("UPDATE warehouse SET w_ytd = w_ytd + {} WHERE w_id = {}".format(h_amount, w_id))

        tx.cur.execute("SELECT d_name, d_street_1, d_street_2, d_city, d_state, d_zip FROM district WHERE d_w_id = {} AND d_id = {} FOR UPDATE".format(w_id, d_id))
        d_name, d_street_1, d_street_2, d_city, d_state, d_zip = tx.cur.fetchone()

        tx.cur.execute("UPDATE district SET d_ytd = d_ytd + {} WHERE d_w_id = {} AND d_id = {}".format(h_amount, w_id, d_id))

        if select_with_c_id_flag:
            # case1
            tx.cur.execute("SELECT c_first, c_middle, c_last, c_street_1, c_street_2, c_city, c_state, c_zip, c_phone, c_since, c_credit, c_credit_lim, c_discount, c_balance FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_id = {}".format(c_w_id, c_d_id, c_id))
            c_first, c_middle, c_last, c_street_1, c_street_2, c_city, c_state, c_zip, c_phone, c_since, c_credit, c_credit_lim, c_discount, c_balance = tx.cur.fetchone()

        else:
            # case2
            tx.cur.execute("SELECT c_id, c_first, c_middle, c_last, c_street_1, c_street_2, c_city, c_state, c_zip, c_phone, c_since, c_credit, c_credit_lim, c_discount, c_balance FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_last = '{}' ORDER BY c_first".format(c_w_id, c_d_id, c_last))
            all_records = tx.cur.fetchall()
            idx = math.ceil(len(all_records) / 2)
            c_id, c_first, c_middle, c_last, c_street_1, c_street_2, c_city, c_state, c_zip, c_phone, c_since, c_credit, c_credit_lim, c_discount, c_balance = all_records[idx-1]

        if c_credit == "BC":
            tx.cur.execute("SELECT c_data FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_id = {}".format(c_w_id, c_d_id, c_id))
            c_data, *_ = tx.cur.fetchone()
            c_data = "{} {} {} {} {} {} | ".format(c_id, c_d_id, c_w_id, d_id, w_id, h_amount) + c_data
            c_data = c_data[0:500]
            tx.cur.execute("UPDATE customer SET c_balance = c_balance - {}, c_ytd_payment = c_ytd_payment + {}, c_payment_cnt = c_payment_cnt + 1, c_data = '{}' WHERE c_w_id = {} AND c_d_id = {} AND c_id = {}".format(h_amount, h_amount, c_data, c_w_id, c_d_id, c_id))
        else:
            tx.cur.execute("UPDATE customer SET c_balance = c_balance - {}, c_ytd_payment = c_ytd_payment + {}, c_payment_cnt = c_payment_cnt + 1 WHERE c_w_id = {} AND c_d_id = {} AND c_id = {}".format(h_amount, h_amount, c_w_id, c_d_id, c_id))

        h_data = w_name + "    " + d_name
        tx.cur.execute("INSERT INTO history (h_c_id, h_c_d_id, h_c_w_id, h_d_id, h_w_id, h_date, h_amount, h_data) VALUES ({}, {}, {}, {}, {}, '{}', {}, '{}')".format(c_id, c_d_id, c_w_id, d_id, w_id, h_date, h_amount, h_data))
            

    except Exception as e:
        # abort during local execution
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
