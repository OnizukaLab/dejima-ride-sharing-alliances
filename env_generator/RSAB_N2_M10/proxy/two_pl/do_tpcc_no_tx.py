import dejimautils
from transaction import Tx
import config
import tpccutils
import random
from datetime import datetime

def doTPCC_NO_2pl():
    # create new tx
    global_xid = dejimautils.get_unique_id()
    tx = Tx(global_xid)
    config.tx_dict[global_xid] = tx

    # prepare parameters
    w_id = random.randint(1, config.warehouse_num)
    d_id = random.randint(1, 10)
    c_id = tpccutils.nurand(1023, 1, 3000, tpccutils.C_FOR_C_ID)
    ol_cnt = random.randint(5, 15)
    rbk = random.randint(1, 100)
    o_entry_d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ol_i_id_list = []
    ol_supply_w_id_list = []
    ol_quantity_list = []
    o_all_local = 1
    for i in range(1, ol_cnt+1):
        if i == ol_cnt and rbk == 1:
            ol_i_id_list.append(None)
        else:
            ol_i_id_list.append(tpccutils.nurand(8191, 1, 100000, tpccutils.C_FOR_OL_I_ID))
        if random.randint(1,100) == 1 or config.warehouse_num == 1:
            ol_supply_w_id_list.append(w_id)
        else:
            o_all_local = 0
            while True:
                ol_supply_w_id = random.randint(1, config.warehouse_num)
                if ol_supply_w_id == w_id:
                    continue
                break
            ol_supply_w_id_list.append(ol_supply_w_id)
        ol_quantity_list.append(random.randint(1, 10))

    # get local locks and check whether miss or not
    try:
        miss_flag = True
        tx.cur.execute("SELECT * FROM warehouse WHERE W_ID = {} FOR SHARE NOWAIT".format(w_id))
        tx.cur.execute("SELECT * FROM district WHERE d_w_id = {} AND d_id = {} FOR UPDATE NOWAIT".format(w_id, d_id))
        tx.cur.execute("SELECT * FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_id = {} FOR SHARE NOWAIT".format(w_id, d_id, c_id))
        if tx.cur.fetchone() != None:
            miss_flag = False
        for i_id in ol_i_id_list:
            if i_id == None:
                continue
            tx.cur.execute("SELECT * FROM item WHERE I_ID = {} FOR SHARE NOWAIT".format(i_id))
            tx.cur.execute("SELECT * FROM stock WHERE s_i_id = {} AND s_w_id = {} FOR SHARE NOWAIT".format(i_id, w_id))
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
        tx.cur.execute("SELECT w_tax FROM warehouse WHERE W_ID = {}".format(w_id))
        w_tax, *_ = tx.cur.fetchone()
        w_tax = float(w_tax)

        tx.cur.execute("SELECT d_tax, d_next_o_id FROM district WHERE d_w_id = {} AND d_id = {} FOR UPDATE".format(w_id, d_id))
        d_tax, d_next_o_id = tx.cur.fetchone()

        tx.cur.execute("SELECT c_discount, c_last, c_credit FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_id = {}".format(w_id, d_id, c_id))
        c_discount, c_last, c_credit = tx.cur.fetchone()

        tx.cur.execute("UPDATE district SET d_next_o_id = d_next_o_id + 1 WHERE d_w_id = {} AND d_id = {}".format(w_id, d_id))

        tx.cur.execute("INSERT INTO oorder (o_id, o_d_id, o_w_id, o_c_id, o_entry_d, o_ol_cnt, o_all_local) VALUES ({}, {}, {}, {}, '{}', {}, {})".format(d_next_o_id, d_id, w_id, c_id, o_entry_d, ol_cnt, o_all_local))

        tx.cur.execute("INSERT INTO new_order (no_o_id, no_d_id, no_w_id) VALUES ({}, {}, {})".format(d_next_o_id, d_id, w_id))

        for i, i_id in enumerate(ol_i_id_list):
            # rollback if i_id is unused value
            if i_id == None:
                raise Exception('i_id = None, rollback')

            tx.cur.execute("SELECT I_PRICE, I_NAME, I_DATA FROM item WHERE I_ID = {}".format(i_id))
            i_price, i_name, i_data = tx.cur.fetchone()

            tx.cur.execute("SELECT s_quantity, s_data, s_dist_01, s_dist_02, s_dist_03, s_dist_04, s_dist_05, s_dist_06, s_dist_07, s_dist_08, s_dist_09, s_dist_10 FROM stock WHERE s_i_id = {} AND s_w_id = {} FOR UPDATE".format(i_id, w_id))
            s_quantity, s_data, *s_dist_list = tx.cur.fetchone()

            if s_quantity - ol_quantity_list[i] >= 10:
                s_quantity = s_quantity - ol_quantity_list[i]
            else:
                s_quantity = s_quantity + 91 - ol_quantity_list[i]
            if o_all_local == 1:
                s_remote_cnt_inc = 0
            else:
                s_remote_cnt_inc = 1
            tx.cur.execute("UPDATE stock SET s_quantity = {}, s_ytd = s_ytd + {}, s_order_cnt = s_order_cnt + 1, s_remote_cnt = s_remote_cnt + {} WHERE s_i_id = {} AND s_w_id = {}".format(s_quantity, ol_quantity_list[i], s_remote_cnt_inc, i_id, w_id))

            ol_dist_info = s_dist_list[d_id - 1]
            tx.cur.execute("INSERT INTO order_line (ol_o_id, ol_d_id, ol_w_id, ol_number, ol_i_id, ol_supply_w_id, ol_quantity, ol_amount, ol_dist_info) VALUES ({}, {}, {}, {}, {}, {}, {}, {}, '{}')".format(d_next_o_id, d_id, w_id, i, i_id, ol_supply_w_id_list[i], ol_quantity_list[i], ol_quantity_list[i] * i_price, ol_dist_info))
            
    except Exception as e:
        # abort during local execution
        tx.abort()
        del config.tx_dict[global_xid]
        return False

    tx.commit()
    del config.tx_dict[global_xid]

    return True
