import falcon
import sys
sys.dont_write_bytecode = True

app = falcon.App()

# FRS
from frs.propagation import FRSPropagation
app.add_route("/frs/_propagate", FRSPropagation())

from frs.termination import FRSTermination
app.add_route("/frs/_terminate", FRSTermination())

from frs.lock import Lock
app.add_route("/_lock", Lock())

from frs.unlock import Unlock
app.add_route("/_unlock", Unlock())

# 2PL
from two_pl.propagation import TPLPropagation
app.add_route("/2pl/_propagate", TPLPropagation())

from two_pl.termination import TPLTermination
app.add_route("/2pl/_terminate", TPLTermination())

# common
# from common.ycsb_load import YCSBLoad
# app.add_route("/load", YCSBLoad())

# from common.ycsb import YCSB
# app.add_route("/ycsb", YCSB())

# from common.tpcc_load_local import TPCCLoadLocal
# app.add_route("/localload_TPCC", TPCCLoadLocal())

# from common.tpcc_load_customer import TPCCLoadCustomer
# app.add_route("/customerload_TPCC", TPCCLoadCustomer())

# from common.tpcc import TPCC
# app.add_route("/tpcc", TPCC())

from common.rsab_load_alliance import RSABLoadAlliance
app.add_route("/load_rsab_alliance", RSABLoadAlliance())

from common.rsab_load_provider import RSABLoadProvider
app.add_route("/load_rsab_provider", RSABLoadProvider())

from common.rsab_alliance import RSABAlliance
app.add_route("/rsab_alliance", RSABAlliance())

from common.rsab_provider import RSABProvider
app.add_route("/rsab_provider", RSABProvider())

from common.execution import execution
app.add_route("/execution", execution())

# from common.rsab_update_trigger import update
# app.add_route("/update", update())

# from common.test import Test
# app.add_route("/_test", Test())

from common.valchange import ValChange
app.add_route("/change_val", ValChange())

# from common.zipf import Zipf
# app.add_route("/zipf", Zipf())

if __name__ == "__main__":
    from wsgiref.simple_server import *
    from socketserver import *
    class ThreadingWsgiServer(ThreadingMixIn, WSGIServer):
        pass

    httpd = make_server('0.0.0.0', 8000, app, ThreadingWsgiServer)
    print("serving on port 8000")
    httpd.serve_forever()
