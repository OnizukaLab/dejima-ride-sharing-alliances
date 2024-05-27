import os
peer_name = os.environ['PEER_NAME'] # peer_name must be calculated at first
import sys
sys.dont_write_bytecode = True
import json

import threading
propagation_lock = threading.Lock()
termination_lock = threading.Lock()
parent_list = {}
is_terminated = {}

# key: global_xid, value: Tx type object
tx_dict = {}

# candidate_record_ids = set()
candidate_record_id_list = []
candidate_v_dict = {}

# sleep time
SLEEP_MS = 0

stmts = []

# config json
with open('dejima_config.json') as f:
    dejima_config_dict = json.load(f)

# prepare dt_list, bt_list
dt_list = [dt for dt in dejima_config_dict['dejima_table'].keys() if peer_name in dejima_config_dict['dejima_table'][dt]]
bt_list = dejima_config_dict['base_table'][peer_name]
if peer_name[0] == 'p':
    sorted_al_list = sorted(dejima_config_dict['alliance_list'][peer_name])

# neighbor peers
neighbor_hop = 2
if peer_name == "alliance0": neighbor_hop = 3
if peer_name[0] == 'p': neighbor_hop = 1
target_peers = {peer_name}
for i in range(neighbor_hop):
    next_target_peers = set()
    for peerlist_for_each_dt in dejima_config_dict["dejima_table"].values():
        peerset_for_each_dt = set(peerlist_for_each_dt)
        if target_peers & peerset_for_each_dt != set():
            next_target_peers = next_target_peers | peerset_for_each_dt
    target_peers = target_peers | next_target_peers
    if 'alliance0' in target_peers: target_peers.remove('alliance0')
target_peers.add('alliance0')
# if peer_name != "alliance0":
target_peers.remove(peer_name)


import time
class TimestampManagement:
    def __init__(self):
        self.duration_time = {'get_xid': 0, 'lock': 0, 'base_update': 0, 'prop_view_0': 0, 'view_udpate': 0, 'prop_view_k': 0, 'communication': 0}
        self.data_num = {'get_xid': 0, 'lock': 0, 'base_update': 0, 'prop_view_0': 0, 'view_udpate': 0, 'prop_view_k': 0, 'communication': 0}
        self.commit_abort_time = {'commit': 0, 'abort': 0}
        self.ca_num = {'commit': 0, 'abort': 0}
        
    def print_timestamps(self, timestamps):
        res = []
        for timestamp in timestamps:
            # short_format = map(lambda time: '{:.2f}'.format(time), timestamp)
            short_format = map(lambda time: float('{:.2f}'.format(time)), timestamp)
            res.append(list(short_format))
        print(res)
        
    def add_duration_time(self, time_name, duration_time):
        self.duration_time[time_name] += duration_time
        self.data_num[time_name] += 1
    
    def add_timestamps(self, timestamps):
        timestamps = list(reversed(timestamps))
        # self.print_timestamps(timestamps)
        for i, timestamp in enumerate(timestamps):
            self.add_duration_time('get_xid', (timestamp[1]-timestamp[0]) + timestamp[4]-timestamp[3])
            self.add_duration_time('lock', timestamp[2]-timestamp[1])
            if i == 0:
                self.add_duration_time('base_update', timestamp[3]-timestamp[2])
                self.add_duration_time('prop_view_0', timestamp[5]-timestamp[4])
            else:
                self.add_duration_time('view_udpate', timestamp[3]-timestamp[2])
                self.add_duration_time('prop_view_k', timestamp[5]-timestamp[4])
            # self.add_duration_time('prop_view_k', timestamp[5]-timestamp[4])
            if i != len(timestamps)-1:
                duration_time = (timestamps[i+1][0]-timestamps[i][5]) + timestamps[i][-1]-timestamps[i+1][-1]
                self.add_duration_time('communication', duration_time)
    
    def commit_or_abort(self, start_time, end_time, ca_type):
        if ca_type in self.ca_num:
            self.commit_abort_time[ca_type] += end_time - start_time
            self.ca_num[ca_type] += 1
        else:
            self.commit_abort_time[ca_type] = end_time - start_time
            self.ca_num[ca_type] = 1
        if ca_type != 'commit':
            self.commit_abort_time['abort'] += end_time - start_time
            self.ca_num['abort'] += 1
    
    def print_result1(self):
        result1 = {'get_xid': 0, 'lock': 0, 'base_update': 0, 'prop_view_0': 0, 'view_udpate': 0, 'prop_view_k': 0, 'communication': 0}
        for key in self.duration_time:
            if self.data_num[key] != 0:
                time = self.duration_time[key] / self.data_num[key]
                result1[key] = float('{:.2f}'.format(time))
        print(json.dumps(result1))
        
    def print_result2(self):
        result2 = []
        for key in self.ca_num:
            if self.ca_num[key] != 0:
                time = self.commit_abort_time[key] / self.ca_num[key]
                result2.append('{}: {}, {:.2f}'.format(key, self.ca_num[key], time))
                # result[key] = float('{:.2f}'.format(time))
        print(',  '.join(result2))
timestamp_management = TimestampManagement()


class TimeMeasurement:
    def __init__(self):
        self.start_time = {}
        self.total_duration_time = {}
        self.data_num = {}
        
    def start_timer(self, time_type, global_xid, s_time=None):
        if time_type not in self.start_time:
            self.start_time[time_type] = {}
        if global_xid not in self.start_time[time_type]:
            self.start_time[time_type][global_xid] = []
        if s_time is None:
            s_time = time.perf_counter()
        self.start_time[time_type][global_xid].append(s_time)
        
    def stop_timer(self, time_type, global_xid, save=True):
        s_time = self.start_time[time_type][global_xid].pop()
        e_time = time.perf_counter()
        if not self.start_time[time_type][global_xid]:
            del self.start_time[time_type][global_xid]
        if save is False:
            return
        if time_type not in self.data_num:
            self.total_duration_time[time_type] = 0
            self.data_num[time_type] = 0
        self.total_duration_time[time_type] += e_time - s_time
        self.data_num[time_type] += 1
        
    def print_time(self):
        duration_time = []
        for time_type, td_time in self.total_duration_time.items():
            num = self.data_num[time_type]
            duration_time.append('{}: {:.2f}'.format(time_type, 1000*td_time/num))
            # duration_time[time_type] = td_time / self.data_num[time_type]
        print(', '.join(duration_time))
time_measurement = TimeMeasurement()



class ResultMeasurement:
    def __init__(self):
        # コミット数 (Updateコミット数+Readコミット数)  コミットの合計時間 (Updateコミットの合計時間+Readコミットの合計時間)
        # アボート数 (Globalアボート数+Localアボート数)  アボートの合計時間 (Globalアボートの合計時間+Localアボートの合計時間)
        self.update_commit_num = 0
        self.read_commit_num = 0
        self.update_commit_time = 0
        self.read_commit_time = 0
        
        self.global_abort_num = 0
        self.local_abort_num = 0
        self.global_abort_time = 0
        self.local_abort_time = 0
        
        self.start_time = 0
        
    def get_result(self, display=False):
        # provider3 |  commit: 8 (2 6)  6.20 (4.10 2.10)[s],   abort: 8 (4 4)  6.20 (4.07 2.13)[s]
        # commit
        commit_num = self.update_commit_num + self.read_commit_num
        commit_num_info = '{} ({} {})'.format(commit_num, self.update_commit_num, self.read_commit_num)
        commit_time = self.update_commit_time + self.read_commit_time
        commit_time_info = '{:.2f} ({:.2f} {:.2f})'.format(commit_time, self.update_commit_time, self.read_commit_time)
        commit_info = 'commit: {}  {}[s]'.format(commit_num_info, commit_time_info)
        # abort
        abort_num = self.global_abort_num + self.local_abort_num
        abort_num_info = '{} ({} {})'.format(abort_num, self.global_abort_num, self.local_abort_num)
        abort_time = self.global_abort_time + self.local_abort_time
        abort_time_info = '{:.2f} ({:.2f} {:.2f})'.format(abort_time, self.global_abort_time, self.local_abort_time)
        abort_info = 'abort: {}  {}[s]'.format(abort_num_info, abort_time_info)
        
        if display:
            print(commit_info)
            print(abort_info)
        return '{} |  {},   {}'.format(peer_name, commit_info, abort_info)
        
    def start_tx(self):
        self.start_time = time.perf_counter()
        
    def commit_tx(self, commit_type):
        commit_time = time.perf_counter() - self.start_time
        if commit_type == 'update':
            self.update_commit_num += 1
            self.update_commit_time += commit_time
        if commit_type == 'read':
            self.read_commit_num += 1
            self.read_commit_time += commit_time
            
    def abort_tx(self, abort_type):
        abort_time = time.perf_counter() - self.start_time
        if abort_type == 'global':
            self.global_abort_num += 1
            self.global_abort_time += abort_time
        if abort_type == 'local':
            self.local_abort_num += 1
            self.local_abort_time += abort_time
result_measurement = ResultMeasurement()