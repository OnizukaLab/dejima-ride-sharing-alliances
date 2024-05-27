import config

class Zipf(object):
    def __init__(self):
        pass

    def on_get(self, req, resp):
        # get params
        params = req.params
        if "theta" in params.keys():
            theta = float(params['theta'])
        else:
            theta = 0.5

        if "record_num" in params.keys():
            record_num = int(params['record_num'])
        else:
            record_num = 100000

        # prepare zipfian series
        config.zipf_gen = config.zipfGenerator(record_num, theta)

        msg = "finished"

        resp.text = msg
        return
