from datetime import datetime
from flask import Flask, request
import json
from hotqueue import HotQueue
import redis
from uuid import uuid4


app = Flask(__name__)
rd = redis.StrictRedis(host='wallen-db', port=6379, db=0)
q = HotQueue('queue', host='wallen-db', port=6379, db=1)


@app.route('/', methods=['GET'])
def instructions():
    return """
    Try these routes:
    
    /             informational
    /run          (GET) job instructions
    /run          (POST) submit job
    /jobs         get list of past jobs
    /jobs/<UUID>  get job results

"""


@app.route('/run', methods=['GET', 'POST'])
def run_job():

    if request.method == 'POST':
        this_uuid = str(uuid4()) 
        this_sequence = str(request.form['seq'])
        data = { 'datetime': str(datetime.now()),
                 'status': 'submitted',
                 'input': this_sequence,
                 'result': 'pending' } 
        rd.hmset(this_uuid, data)

        q.put(this_uuid)
        return f'Job {this_uuid} submitted to the queue\n'

#        response = requests.post(url='http://wallen-api:5000/job', json={'uuid': this_uuid, 'sequence': this_sequence})
#        if response.status_code == 200 or response.status_code == 201:
#            rd.hset(this_uuid, 'status', f'success, {response.status_code}')
#        else:
#            rd.hset(this_uuid, 'status', f'failure, {response.status_code}')
#        return f'JOBID = {this_uuid}\n'

    else:
        return """
    This is a route for POSTing sequences to run. Use the form:

    curl -X POST -d "seq=AAAAA" localhost:5041/run

    Where the sequence "AAAAA" is what you want to analyze.

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

