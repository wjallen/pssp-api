from datetime import datetime
from flask import Flask, request
import json
from hotqueue import HotQueue
import redis
import os
from uuid import uuid4


redis_ip = os.environ.get('REDIS_IP')
if not redis_ip:
    raise Exception()


app = Flask(__name__)
rd = redis.StrictRedis(host=redis_ip, port=6379, db=0)
q = HotQueue('queue', host=redis_ip, port=6379, db=1)


@app.route('/', methods=['GET'])
def instructions():
    return """
    Try these routes:
    
    /             informational
    /run          (GET) job instructions
    /run          (POST) submit job
    /jobs         get list of past jobs
    /jobs/<UUID>  get job results
    /delete       (GET) delete instructions
    /delete       (DELETE) delete job

"""


@app.route('/run', methods=['GET', 'POST'])
def run_job():

    if request.method == 'POST':
        this_uuid = str(uuid4()) 
        this_sequence = str(request.form['seq'])
        data = { 'datetime': str(datetime.now()),
                 'status': 'submitted',
                 'input': this_sequence }
        rd.hmset(this_uuid, data)

        q.put(this_uuid)
        return f'Job {this_uuid} submitted to the queue\n'

    else:
        return """
    This is a route for POSTing sequences to run. Use the form:

    curl -X POST -d "seq=AAAAA" localhost:5041/run

    Where the sequence "AAAAA" is what you want to analyze.

"""


@app.route('/delete', methods=['GET', 'DELETE'])
def delete_job():

    if request.method == 'DELETE':
        this_jobid = str(request.form['jobid'])
        rd.delete(this_jobid)
        return f'Job {this_jobid} deleted\n'

    else:
        return """
    This is a route for DELETE-ing former jobs. Use the form:

    curl -X DELETE -d "jobid=asdf1234" localhost:5041/delete

    Where the jobid "asdf1234" is what you want to delete.

"""


@app.route('/jobs', methods=['GET'])
def get_jobs():
    redis_dict = {}
    for key in rd.keys():
        redis_dict[str(key.decode('utf-8'))] = {}
        redis_dict[str(key.decode('utf-8'))]['datetime'] = rd.hget(key, 'datetime').decode('utf-8')
        redis_dict[str(key.decode('utf-8'))]['status'] = rd.hget(key, 'status').decode('utf-8')
    return json.dumps(redis_dict, indent=4)


@app.route('/jobs/<jobuuid>', methods=['GET'])
def get_job_output(jobuuid):
    bytes_dict = rd.hgetall(jobuuid)
    final_dict = {}
    for key, value in bytes_dict.items():
        if key.decode('utf-8') == 'result':
            final_dict[key.decode('utf-8')] = json.loads(value.decode('utf-8'))
        else:
            final_dict[key.decode('utf-8')] = value.decode('utf-8')
    return json.dumps(final_dict, indent=4)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

