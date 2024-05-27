import random, string
import config
import threading

COL_N = 10
COND_N = 10

def randomname(n):
   return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def get_stmt_for_load(start_id, record_num, step):
    # prepare cols name
    col_names = ['ID']
    for i in range(COL_N):
        col_names.append("COL{}".format(i+1))
    col_names.append("lineage")
    for i in range(COND_N):
        col_names.append("COND{}".format(i+1))

    # create bulk insert statement
    stmt = "INSERT INTO bt (" + ",".join(col_names) + ") VALUES "
    records = []
    for i in range(start_id, start_id + record_num * step, step):
        cols = []
        conds = []
        for _ in range(COL_N):
            cols.append("'"+str(randomname(10))+"'")
        for _ in range(COND_N):
            conds.append(str(random.randint(0, 99)))
        record = "(" + ",".join([str(i)] + cols + ["'"+config.peer_name+"-bt-"+str(i)+"'"] + conds) + ")"
        records.append(record)
    stmt = stmt + ",".join(records)
    return stmt

def get_workload_for_ycsb(read_num=5, write_num=5):
    stmts = []
    # Read
    for i in range(read_num):
        target_col = 'col{}'.format(random.randint(1,COL_N))
        stmts.append("SELECT {} FROM bt WHERE id={}".format(target_col, next(zipf_gen)))
    # Write
    for i in range(write_num):
        target_col = 'col{}'.format(random.randint(1,COL_N))
        stmts.append("UPDATE bt SET {}='{}' WHERE id={}".format(target_col, randomname(10), next(zipf_gen)))
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