from datetime import datetime
from flask import Flask
import json
import redis
import requests
from uuid import uuid4


app = Flask(__name__)
rd = redis.StrictRedis(host='wallen-db', port=6379, db=0)


@app.route('/', methods=['GET'])
def instructions():
    return """
    Try these routes:
    
    /             this page
    /run/<AAA>    submit job
    /jobs         get past jobs
    /jobs/<UUID>  get job result

"""


@app.route('/run/<sequence>', methods=['GET'])
def run_job(sequence):
    this_uuid = str(uuid4()) 
    this_time = str(datetime.now())
    rd.hset(this_uuid, 'datetime', this_time)
    rd.hset(this_uuid, 'status', 'submitted')
    rd.hset(this_uuid, 'input', sequence)
    rd.hset(this_uuid, 'result', 'pending')
    response = requests.post(url='http://wallen-api:5000/job', json={'uuid': this_uuid, 'sequence': sequence})
    if response.status_code == 200 or response.status_code == 201:
        rd.hset(this_uuid, 'status', f'success, {response.status_code}')
    else:
        rd.hset(this_uuid, 'status', f'failure, {response.status_code}')
    return f'JOBID = {this_uuid}\n'


@app.route('/jobs', methods=['GET'])
def get_jobs():
    redis_dict = {}
    for key in rd.keys():
        redis_dict[str(key.decode('utf-8'))] = {}
        redis_dict[str(key.decode('utf-8'))]['datetime'] = rd.hget(key, 'datetime').decode('utf-8')
        redis_dict[str(key.decode('utf-8'))]['status'] = rd.hget(key, 'status').decode('utf-8')
    return json.dumps(redis_dict, indent=2)


@app.route('/jobs/<jobuuid>', methods=['GET'])
def get_job_output(jobuuid):
    bytes_dict = rd.hgetall(jobuuid)
    final_dict = {}
    final_dict['input'] = rd.hget(jobuuid, b'input').decode('utf-8')
    final_dict['status'] = rd.hget(jobuuid, b'status').decode('utf-8')
    final_dict['datetime'] = rd.hget(jobuuid, b'datetime').decode('utf-8')
    final_dict['result'] = json.loads(rd.hget(jobuuid, b'result').decode('utf-8'))

    #normal_dict = {}
    #for key, value in bytes_dict.items():
    #    if key is 'result':
    #        normal_dict[key.decode('utf-8')] = json.loads(value.decode('utf-8'))
    #    else:
    #        normal_dict[key.decode('utf-8')] = value.decode('utf-8')
    return json.dumps(final_dict, indent=2)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

