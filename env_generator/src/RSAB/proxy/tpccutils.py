import random, string
import config
from datetime import datetime

COND_N = 10
WAREHOUSE_NUM = 1
NAME_TOKENS = ["BAR", "OUGHT", "ABLE", "PRI", "PRES", "ESE", "ANTI", "CALLY", "ATION", "EING"]
random.seed(0)
C_FOR_C_LAST = random.randint(0, 255)
C_FOR_C_ID = random.randint(0, 1023)
C_FOR_OL_I_ID = random.randint(0, 8191)

def randomStr(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def nurand(A, x, y, C):
    return ((random.randint(0, A) | random.randint(x, y)) + C) % (y - x + 1) + x

def get_last(num):
    return NAME_TOKENS[int(num/100)] + NAME_TOKENS[int(num/10) % 10] + NAME_TOKENS[num % 10]

def get_loadstmt_for_item():
    random.seed(1)
    item_loadstmt = "INSERT INTO item (i_id, i_im_id, i_name, i_price, i_data) VALUES "
    items_num = 100000
    records = []
    for i in range(1, items_num + 1):
        i_id = i
        i_im_id = random.randint(1, items_num)
        i_name = randomStr(random.randint(14,24))
        i_price = random.randint(100, 10000) / 100
        i_data_len = random.randint(26, 50)
        if random.randint(0, 99) < 90:
            # 90 % of records is random string
            i_data = randomStr(i_data_len)
        else:
            # 10 % of records includes "ORIGINAL"
            start_ORIGINAL = random.randint(0, i_data_len-8)
            i_data = randomStr(start_ORIGINAL) + "ORIGINAL" + randomStr(i_data_len - 8 - start_ORIGINAL)
        records.append("({}, {}, '{}', {}, '{}')".format(i_id, i_im_id, i_name, i_price, i_data))
    item_loadstmt = item_loadstmt + ",".join(records)
    return item_loadstmt

def get_loadstmt_for_warehouse(w_id):
    random.seed(2)
    warehouse_loadstmt = "INSERT INTO warehouse (w_id, w_ytd, w_tax, w_name, w_street_1, w_street_2, w_city, w_state, w_zip) VALUES "
    records = []

    w_ytd = 300000
    w_tax = random.randint(0, 2000) / 10000
    w_name = randomStr(random.randint(6, 10))
    w_street_1 = randomStr(random.randint(10, 20))
    w_street_2 = randomStr(random.randint(10, 20))
    w_city = randomStr(random.randint(10, 20))
    w_state = randomStr(2).upper()
    w_zip = "".join(random.choices("0123456789", k=4)) + "11111"
    records.append("({}, {}, {}, '{}', '{}', '{}', '{}', '{}', '{}')".format(w_id, w_ytd, w_tax, w_name, w_street_1, w_street_2, w_city, w_state, w_zip))

    warehouse_loadstmt = warehouse_loadstmt + ",".join(records)
    return warehouse_loadstmt

def get_loadstmt_for_stock(w_id, start_s_i_id):
    random.seed(start_s_i_id)
    stock_loadstmt = "INSERT INTO stock (s_w_id, s_i_id, s_quantity, s_ytd, s_order_cnt, s_remote_cnt, s_data, s_dist_01, s_dist_02, s_dist_03, s_dist_04, s_dist_05, s_dist_06, s_dist_07, s_dist_08, s_dist_09, s_dist_10) VALUES "
    records = []
    # items_num = 100000, then error occured (postgres server internal error)
    items_num = 20000

    s_w_id = w_id
    for j in range(start_s_i_id, start_s_i_id + items_num):
        s_i_id = j
        s_quantity = random.randint(10, 100)
        s_ytd = 0
        s_order_cnt = 0
        s_remote_cnt = 0
        s_data_len = random.randint(26, 50)
        if random.randint(0, 99) < 90:
            # 90 % of records is random string
            s_data = randomStr(s_data_len)
        else:
            # 10 % of records includes "ORIGINAL"
            start_ORIGINAL = random.randint(0, s_data_len-8)
            s_data = randomStr(start_ORIGINAL) + "ORIGINAL" + randomStr(s_data_len - 8 - start_ORIGINAL)
        s_dist_xx = ",".join(["'{}'".format(randomStr(24)) for _ in range(10)])
        records.append("({},{},{},{},{},{},'{}',{})".format(s_w_id, s_i_id, s_quantity, s_ytd, s_order_cnt, s_remote_cnt, s_data, s_dist_xx))
    
    stock_loadstmt = stock_loadstmt + ",".join(records)
    return stock_loadstmt
            
def get_loadstmt_for_district(w_id):
    random.seed(4)
    district_loadstmt = "INSERT INTO district (d_w_id, d_id, d_ytd, d_tax, d_next_o_id, d_name, d_street_1, d_street_2, d_city, d_state, d_zip) VALUES "
    records = []

    d_w_id = w_id
    for j in range(1, 10+1):
        d_id = j
        d_ytd = 30000
        d_tax = random.randint(0, 2000) / 10000
        d_next_o_id = 3001
        d_name = randomStr(random.randint(6, 10))
        d_street_1 = randomStr(random.randint(10, 20))
        d_street_2 = randomStr(random.randint(10, 20))
        d_city = randomStr(random.randint(10, 20))
        d_state = randomStr(2).upper()
        d_zip = "".join(random.choices("0123456789", k=4)) + "11111"
        records.append("({},{},{},{},{},'{}','{}','{}','{}','{}','{}')".format(d_w_id, d_id, d_ytd, d_tax, d_next_o_id, d_name, d_street_1, d_street_2, d_city, d_state, d_zip))
    
    district_loadstmt = district_loadstmt + ",".join(records)
    return district_loadstmt
            
def get_loadstmt_for_customer_history(w_id, d_id):
    random.seed(w_id+d_id)
    customer_loadstmt = "INSERT INTO customer (c_w_id, c_d_id, c_id, c_discount, c_credit, c_last, c_first, c_credit_lim, c_balance, c_ytd_payment, c_payment_cnt, c_delivery_cnt, c_street_1, c_street_2, c_city, c_state, c_zip, c_phone, c_middle, c_data, c_lineage, c_cond01, c_cond02, c_cond03, c_cond04, c_cond05, c_cond06, c_cond07, c_cond08, c_cond09, c_cond10) VALUES "
    history_loadstmt = "INSERT INTO history (h_c_id, h_c_d_id, h_c_w_id, h_d_id, h_w_id, h_amount, h_data) VALUES "
    customer_records = []
    history_records = []

    c_w_id = w_id
    h_c_w_id = c_w_id
    h_w_id = c_w_id
    c_d_id = d_id # given d_id (e.g. Peer1 has records with d_id=1)
    h_c_d_id = c_d_id
    h_d_id = c_d_id
    for j in range(1, 3000+1):
        c_id = j
        h_c_id = c_id
        c_discount = random.randint(1, 5000) / 10000
        if random.randint(0, 99) < 10:
            c_credit = "BC" # 10 % = Bad Credit
        else:
            c_credit = "GC" # 90 % = Good Credit
        if j <= 1000:
            c_last = get_last(j-1) # first 1000 customer's last name is generated by [0, ..., 999]
        else:
            c_last = get_last(nurand(255, 0, 999, C_FOR_C_LAST)) # 2000 customer is generated non-uniform randomly
        c_first = randomStr(random.randint(8,16))
        c_credit_lim = 50000
        c_balance = -10
        c_ytd_payment = 10
        c_payment_cnt = 1
        c_delivery_cnt = 0
        c_street_1 = randomStr(random.randint(10, 20))
        c_street_2 = randomStr(random.randint(10, 20))
        c_city = randomStr(random.randint(10, 20))
        c_state = randomStr(2).upper()
        c_zip = "".join(random.choices("0123456789", k=4)) + "11111"
        c_phone = "".join(random.choices("0123456789", k=16))
        c_middle = "OE";
        c_data = randomStr(random.randint(300, 500))
        h_amount = 10
        h_data = randomStr(random.randint(10, 24))
        c_lineage = config.peer_name + "-" + "customer" + "-" + "({},{},{})".format(c_w_id, c_d_id, c_id)
        c_condxx = ",".join([str(random.randint(0,99)) for _ in range(10)])

        customer_records.append("({},{},{},{},'{}','{}','{}',{},{},{},{},{},'{}','{}','{}','{}','{}','{}','{}','{}','{}',{})".format(c_w_id, c_d_id, c_id, c_discount, c_credit, c_last, c_first, c_credit_lim, c_balance, c_ytd_payment, c_payment_cnt, c_delivery_cnt, c_street_1, c_street_2, c_city, c_state, c_zip, c_phone, c_middle, c_data, c_lineage, c_condxx))
        history_records.append("({},{},{},{},{},{},'{}')".format(h_c_id, h_c_d_id, h_c_w_id, h_d_id, h_w_id, h_amount, h_data))

    customer_loadstmt = customer_loadstmt + ",".join(customer_records)
    history_loadstmt = history_loadstmt + ",".join(history_records)
    return customer_loadstmt, history_loadstmt

def get_loadstmt_for_orders_neworders_orderline(w_id, d_id):
    random.seed(w_id + d_id)
    order_loadstmt = "INSERT INTO oorder (o_w_id, o_d_id, o_id, o_c_id, o_carrier_id, o_ol_cnt, o_all_local, o_entry_d) VALUES "
    orderline_loadstmt = "INSERT INTO order_line (ol_o_id, ol_d_id, ol_w_id, ol_number, ol_i_id, ol_supply_w_id, ol_quantity, ol_amount, ol_delivery_d, ol_dist_info) VALUES "
    neworder_loadstmt = "INSERT INTO new_order (no_o_id, no_d_id, no_w_id) VALUES "

    perm = list(range(1, 3001))
    random.shuffle(perm)

    order_records = []
    orderline_records = []
    neworder_records = []

    o_w_id = w_id
    o_d_id = d_id
    for j in range(1, 3001):
        o_id = j
        o_c_id = perm[j-1]
        if o_id < 2101:
            o_carrier_id = random.randint(1, 10)
        else:
            o_carrier_id = "NULL"
        o_ol_cnt = random.randint(5, 15)
        o_all_local = 1
        o_entry_d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_records.append("({},{},{},{},{},{},{},'{}')".format(o_w_id, o_d_id, o_id, o_c_id, o_carrier_id, o_ol_cnt, o_all_local, o_entry_d))
        
        no_o_id = o_id
        if no_o_id > 2100:
            no_d_id = o_d_id
            no_w_id = o_w_id
            neworder_records.append("({},{},{})".format(no_o_id, no_d_id, no_w_id))
        
        for k in range(1, o_ol_cnt + 1):
            ol_o_id = o_id
            ol_d_id = o_d_id
            ol_w_id = o_w_id
            ol_number = k
            ol_i_id = random.randint(1, 100000)
            ol_supply_w_id = o_w_id
            ol_quantity = 5
            if ol_o_id < 2101:
                ol_amount = 0
                ol_delivery_d = "'{}'".format(o_entry_d)
            else:
                ol_amount = random.randint(1,999999) / 100
                ol_delivery_d = "NULL"
            ol_dist_info = randomStr(24)
            orderline_records.append("({},{},{},{},{},{},{},{},{},'{}')".format(ol_o_id, ol_d_id, ol_w_id, ol_number, ol_i_id, ol_supply_w_id, ol_quantity, ol_amount, ol_delivery_d, ol_dist_info))

    order_loadstmt = order_loadstmt + ",".join(order_records)
    orderline_loadstmt = orderline_loadstmt + ",".join(orderline_records)
    neworder_loadstmt = neworder_loadstmt + ",".join(neworder_records)
    return order_loadstmt, orderline_loadstmt, neworder_loadstmt

def get_stmt_for_no(w_id, d_id, c_id):
    ret_stmts = []
    ret_stmts.append("SELECT w_tax FROM warehouse WHERE W_ID = {}".format(w_id))
    ret_stmts.append("SELECT d_tax, d_next_o_id FROM district WHERE d_w_id = {} AND d_id = {} FOR UPDATE".format(w_id, d_id))
    ret_stmts.append("SELECT c_discount, c_last, c_credit FROM customer WHERE c_w_id = {} AND c_d_id = {} AND c_id = {}".format(w_id, d_id, c_id))
    ret_stmts.append("UPDATE district SET d_next_o_id = d_next_o_id + 1 WHERE d_w_id = {} AND d_id = {}".format(w_id, d_id))
    ret_stmts.append("INSERT INTO orders (o_id, o_d_id, o_w_id, o_c_id, o_entry_d, o_ol_cnt, o_all_local) VALUES ({}, {}, {}, {}, {}, {}, {})".format(w_id, d_id))

    pass