import time
import config
import random
from frs.do_rsab_alliance_tx import doRSAB_ALLIANCE_frs
from two_pl.do_rsab_alliance_tx import doRSAB_ALLIANCE_2pl

class RSABAlliance(object):
    def __init__(self):
        pass

    def on_get(self, req, resp):
        # get params
        params = req.params
        param_keys = ["bench_time", "method"]
        for key in param_keys:
            if not key in params.keys():
                msg = "Invalid parameters"
                resp.text = msg
                return
        bench_time = int(params['bench_time'])
        METHOD = params['method']
            
        # benchmark
        switch_cnt = []
        start_time = time.time()
        print("benchmark start")
        random.seed()
        
        alliance_num = int(config.peer_name[8:])
        random.seed(2*alliance_num)
        config.stmts = []
        
        # initialize
        config.timestamp_management = config.TimestampManagement()
        config.time_measurement = config.TimeMeasurement()
        config.result_measurement = config.ResultMeasurement()

        # frs & 2pl
        if METHOD == "frs" or METHOD == "2pl":
            if METHOD == "frs":
                doRSAB = doRSAB_ALLIANCE_frs
            else:
                doRSAB = doRSAB_ALLIANCE_2pl
            
            current_time = time.time() - start_time
            while (current_time < bench_time):
                current_time = time.time() - start_time
                doRSAB()

        # hybrid
        elif METHOD == "hybrid":
            current_method = "2pl"
            doRSAB = doRSAB_ALLIANCE_2pl
            check_time = 30
            check_interval = 300
            test_time = int(params.get('test_time', 0))
            # determine first check timing
            next_check = random.randint(0,check_interval - check_time * 2 - 2)

            temp_commit = {'before': {'commit': 0, 'abort': 0}, 'after': {'commit': 0, 'abort': 0}}
            temp_changed_mode_flag = False

            current_time = time.time() - start_time
            while (current_time < test_time):
                current_time = time.time() - start_time
                # normal mode
                if current_time < next_check:
                    doRSAB()

                # check mode
                # before
                elif current_time < next_check + check_time:
                    result = doRSAB()
                    if result == True:
                        temp_commit['before']['commit'] += 1
                    elif result == False:
                        temp_commit['before']['abort'] += 1
                # after
                elif current_time < next_check + check_time * 2:
                    # change method if this is first time
                    if not temp_changed_mode_flag:
                        temp_changed_mode_flag = True
                        if current_method == "2pl":
                            current_method = "frs"
                            doRSAB = doRSAB_ALLIANCE_frs
                        else:
                            current_method = "2pl"
                            doRSAB = doRSAB_ALLIANCE_2pl

                    result = doRSAB()
                    if result == True:
                        temp_commit['after']['commit'] += 1
                    elif result == False:
                        temp_commit['after']['abort'] += 1

                # return to normal, don't execute Tx
                else:
                    next_check += check_interval
                    if temp_commit['after']['commit'] < temp_commit['before']['commit']:
                        switch_cnt.append(0)
                        if current_method == "2pl":
                            current_method = "frs"
                            doRSAB = doRSAB_ALLIANCE_frs
                        else:
                            current_method = "2pl"
                            doRSAB = doRSAB_ALLIANCE_2pl
                    else:
                        switch_cnt.append(1)
                        if current_method == "2pl":
                            print("{:.2f}: FRS -> 2PL  ({} -> {})".format(current_time, temp_commit['before']['commit'], temp_commit['after']['commit']))
                        else:
                            print("{:.2f}: S2PL -> FRS  ({} -> {})".format(current_time, temp_commit['before']['commit'], temp_commit['after']['commit']))

                    temp_changed_mode_flag = False
                    temp_commit = {'before': {'commit': 0, 'abort': 0}, 'after': {'commit': 0, 'abort': 0}}
                    continue
            
            if bench_time != 0:
                current_time = time.time() - start_time
                bench_start_time = test_time + 5
                time.sleep(bench_start_time - current_time)
                
                config.timestamp_management = config.TimestampManagement()
                config.time_measurement = config.TimeMeasurement()
                config.result_measurement = config.ResultMeasurement()
                
                start_time = time.time()
                current_time = time.time() - start_time
                while (current_time < bench_time):
                    current_time = time.time() - start_time
                    doRSAB()

        # invalid method
        else:
            resp.text = "invalid method"
            return

        # if switch_cnt != []:
        #     msg += " *" + " ".join(map(str, switch_cnt)) + "*"
        
        config.timestamp_management.print_result1()
        config.time_measurement.print_time()
        msg = config.result_measurement.get_result(display=True)
        msg += "\n"

        print("benchmark finished")
        resp.text = msg
        return
