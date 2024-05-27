import random, string
import config
import threading

COL_N = 10
COND_N = 10
LOCK_DEBUG = False
ZIPF_GEN_MODE = False
QUERY_ORDER = True
READ_WRITE_RATE = 0
RECORDS_TX = 4
RECORDS_PEER = 10

def randomname(n):
   return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def get_stmt_for_load(start_id, record_num, step):
    # prepare cols name
    col_names = ["V", "L", "D", "R"] + config.sorted_al_list + ["LINEAGE"]

    # create bulk insert statement
    stmt = "INSERT INTO bt (" + ",".join(col_names) + ") VALUES "
    records = []
    for i in range(start_id, start_id + record_num * step, step):
        cols = []
        
        cols.append(str(random.randint(1, 9999)))
        cols.append(str(random.randint(1, 9999)))
        cols.append('0')
        for j in range(len(config.sorted_al_list)):
            cols.append("'true'")
        
        record = "(" + ",".join([str(i)] + cols + ["'"+config.peer_name+"-bt-"+str(i)+"'"]) + ")"
        records.append(record)
        # config.candidate_record_ids.add(i)
        config.candidate_record_id_list.append(i)
    # config.candidate_record_id_list = list(config.candidate_record_ids)
    # config.candidate_record_id_list = [start_id]
        
    stmt = stmt + ",".join(records)
    return stmt

def get_workload_for_provider():
    if config.stmts and QUERY_ORDER == True:
        return config.stmts
    stmts = []
    V_list = random.sample(config.candidate_record_id_list, RECORDS_TX)
    if ZIPF_GEN_MODE == True:
        index = next(zipf_gen)-1
        V_list = [config.candidate_record_id_list[index]]
    if random.randint(1, 100) <= READ_WRITE_RATE:
        for V in V_list:
            stmts.append("SELECT * FROM bt WHERE V={}".format(V))
    else:
        if LOCK_DEBUG: print(V_list)
        for V in V_list:
            L = random.randint(1, 9999)
            stmts.append("UPDATE bt SET L={}, R=0 WHERE V={}".format(L, V))
    config.stmts = stmts
    return stmts
    
def get_workload_for_alliance0():
    if config.stmts and QUERY_ORDER == True:
        return config.stmts
    stmts = []
    keys = random.sample(list(config.candidate_v_dict.keys()), RECORDS_TX)
    VA_list = [random.choice(config.candidate_v_dict[key]) for key in keys]
    if ZIPF_GEN_MODE == True:
        index = next(zipf_gen)-1
        
        n = RECORDS_PEER
        lower_bound = index//n * n
        upper_bound = lower_bound+n
        index = random.randint(lower_bound, upper_bound-1)
        v = index + 1
        
        VA_list = [random.choice(config.candidate_v_dict[v])]
    if random.randint(1, 100) <= READ_WRITE_RATE:
        # VA_list = random.sample(config.candidate_record_id_list, 2)
        for VA in VA_list:
            stmts.append("SELECT * FROM mt WHERE V={} AND A={}".format(VA[0], VA[1]))
    else:
        if LOCK_DEBUG: print(keys)
        # VA_list = random.sample(config.candidate_record_id_list, 2)
        for VA in VA_list:
            D = random.randint(1, 9999)
            stmts.append("UPDATE mt SET D={}, R=1 WHERE V={} AND A={}".format(D, VA[0], VA[1]))
    config.stmts = stmts
    return stmts
    
def get_workload_for_alliance():
    if config.peer_name == "alliance0": return get_workload_for_alliance0()
    if config.stmts and QUERY_ORDER == True:
        return config.stmts
    stmts = []
    V_list = random.sample(config.candidate_record_id_list, RECORDS_TX)
    if ZIPF_GEN_MODE == True:
        index = next(zipf_gen)-1
        
        n = RECORDS_PEER
        lower_bound = index//n * n
        upper_bound = lower_bound+n
        index = random.randint(lower_bound, upper_bound-1)
        
        V_list = [config.candidate_record_id_list[index]]
    if random.randint(1, 100) <= READ_WRITE_RATE:
        for V in V_list:
            stmts.append("SELECT * FROM mt WHERE V={}".format(V))
    else:
        if LOCK_DEBUG: print(V_list)
        for V in V_list:
            D = random.randint(1, 9999)
            stmts.append("UPDATE mt SET D={}, R=1 WHERE V={}".format(D, V))
    config.stmts = stmts
    return stmts

# prepare zipf generator
class zipfGenerator:
    def __init__(self, n, theta):
        self.n = n
        self.theta = theta
        self.alpha = 1 / (1-theta)
        self.zetan = self.zeta(n, theta)
        self.eta = (1 - pow(2.0/n, 1-theta)) / (1 - self.zeta(2, theta) / self.zetan)
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            u = random.random()
            uz = u * self.zetan
            if uz < 1:
                return 1
            elif uz < 1 + pow(0.5, self.theta):
                return 2
            else:
                return 1 + int(self.n * pow(self.eta * u - self.eta + 1, self.alpha))

    def zeta(self, n, theta):
        sum = 0
        for i in range(1,n+1):
            sum += 1 / pow(i, theta)
        return sum