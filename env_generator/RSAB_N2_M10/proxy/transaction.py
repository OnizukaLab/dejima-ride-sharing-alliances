from pool import pool
from psycopg2.extras import DictCursor

class Tx:
    def __init__(self, global_xid):
        self.global_xid = global_xid
        self.db_conn = pool.getconn(key=global_xid)
        self.child_peers = []
        self.cur = self.db_conn.cursor(cursor_factory=DictCursor)
        self.propagation_cnt = 0
    
    def commit(self):
        self.cur.close()
        self.db_conn.commit()
        pool.putconn(self.db_conn)

    def abort(self):
        self.cur.close()
        self.db_conn.rollback()
        pool.putconn(self.db_conn)

    def extend_childs(self, target_peers):
        self.child_peers.extend(target_peers)

    def reset_childs(self):
        self.child_peers = []