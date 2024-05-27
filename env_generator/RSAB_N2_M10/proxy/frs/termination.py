import json
import dejimautils
import config
import time

class FRSTermination(object):
    def __init__(self):
        pass

    def on_post(self, req, resp):
        time.sleep(config.SLEEP_MS * 0.001)

        if req.content_length:
            body = req.bounded_stream.read()
            params = json.loads(body)

        if params['result'] == "commit":
            commit = True
        else:
            commit = False

        global_xid = params['xid']
        src_peer = params["src_peer"]
        
        with config.termination_lock:
            if global_xid not in config.tx_dict or config.peer_name == src_peer or global_xid in config.is_terminated:
                resp.text = json.dumps({"result": "Ack"})
                return
            config.is_terminated[global_xid] = True
        
        tx = config.tx_dict[global_xid]
        
        # termination
        terminated_peers = []
        if commit:
            tx.commit()
            res = dejimautils.termination_request("commit", global_xid, "frs", src_peer)
        else:
            tx.abort()
            res = dejimautils.termination_request("abort", global_xid, "frs", src_peer)
        
        if global_xid in config.parent_list:
            del config.parent_list[global_xid]
        del config.tx_dict[global_xid]
        del config.is_terminated[global_xid]
        
        if isinstance(res, list):
            terminated_peers = res
        terminated_peers.append(config.peer_name)
        
        msg = {"result": "Ack", "terminated_peers": terminated_peers}
        resp.text = json.dumps(msg)
        return