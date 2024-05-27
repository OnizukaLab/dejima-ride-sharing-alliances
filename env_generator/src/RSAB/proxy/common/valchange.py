import config
import rsabutils
import random

class ValChange(object):
    def __init__(self):
        pass

    def on_get(self, req, resp):
        # get params
        params = req.params
        
        about = params['about']
        
        if about == 'zipf' and not float(params['theta']) < -0.1:
            theta = float(params['theta'])
            rsabutils.ZIPF_GEN_MODE = True
            rsabutils.RECORDS_TX = 1
            record_num = len(config.candidate_record_id_list)
            rsabutils.zipf_gen = rsabutils.zipfGenerator(record_num, theta)
            print('set zipf {}'.format(theta))
            # # Visualization of output
            # output_dict = {}
            # for _ in range(100000):
            #     index = next(rsabutils.zipf_gen)-1
            #     if config.peer_name.startswith('alliance'):
            #         n = rsabutils.RECORDS_PEER
            #         lower_bound = index//n * n
            #         upper_bound = lower_bound+n
            #         index = random.randint(lower_bound, upper_bound-1)
                
            #     id = config.candidate_record_id_list[index]
            #     if id not in output_dict:
            #         output_dict[id] = 0
            #     output_dict[id] += 1
            # output_dict = dict(sorted(output_dict.items(), key=lambda x: x[0]))
            # print(config.candidate_record_id_list)
            # print(output_dict)
                
        elif about == 'zipf' and float(params['theta']) < 0:
            rsabutils.ZIPF_GEN_MODE = False
            print('set zipf off')
            
            
        elif about == 'set_read_write_rate':
            rate = int(params['rate'])
            rsabutils.READ_WRITE_RATE = rate
            print('set read-write-rate {}'.format(rate))
        
        
        elif about == 'set_records_tx':
            records_tx = int(params['records_tx'])
            rsabutils.RECORDS_TX = records_tx
            print('set num of records per Tx {}'.format(records_tx))
            
        
        elif about == 'set_query_order':
            on_off = params['on_off']
            if on_off == 'off' or on_off == 'OFF':
                rsabutils.QUERY_ORDER = False
                print('set query_order off')
            elif on_off == 'on' or on_off == 'ON':
                rsabutils.QUERY_ORDER = True
                print('set query_order on')
            else:
                print('query_order parameter error')
            
        elif about == 'show_lock':
            lock_list = list(config.tx_dict)
            print('remaining lock: {}'.format(lock_list))
            
        msg = "finished"
        resp.text = msg
        return