from hotqueue import HotQueue
import json
import os
import redis
import subprocess


redis_ip = os.environ.get('REDIS_IP')
if not redis_ip:
    raise Exception()


rd = redis.StrictRedis(host=redis_ip, port=6379, db=0, decode_responses=True)
q = HotQueue('queue', host=redis_ip, port=6379, db=1)


@q.worker
def run_pssp_job(job):

    subprocess.run(["sleep 20"], shell=True, check=True)

    data = rd.hgetall(job)
    this_sequence = data['input']

    subprocess.run(['mkdir -p /analyze/temp'], shell=True, check=True)
    with open('/analyze/sequence.fasta', 'w') as out:
        out.write(f'>JOBID = {job}\n')
        out.write(f'{this_sequence}\n')
    subprocess.run(['/Predict_Property/Predict_Property.sh -i /analyze/sequence.fasta -o /analyze/temp'], shell=True, check=True) 

    output = []

    with open('/analyze/temp/sequence.all') as f:
        for _ in range(8):
            line = next(f).strip()
            output.append(line)

    result = {}
    result['HED'] = output[0]
    result['INP'] = output[1]
    result['SS3'] = output[2]
    result['SS8'] = output[3]
    result['ACC'] = output[4]
    result['DIS'] = output[5]
    result['TM2'] = output[6]
    result['TM8'] = output[7]

    rd.hset(job, 'result', json.dumps(result))
    rd.hset(job, 'status', 'finished')

    return


run_pssp_job()


