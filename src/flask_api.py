from flask import Flask, request
from flask_restful import reqparse, Resource, Api
import json
import redis
import subprocess


app = Flask(__name__)
api = Api(app)

rd = redis.StrictRedis(host='wallen-db', port=6379, db=0)


class RunTest(Resource):
    def get(self):
        return {'status': 'test works'}


class RunJob(Resource):
    def post(self):
        data = request.get_json(force=True)
        this_uuid = data['uuid']
        sequence = data['sequence']

        subprocess.run(['mkdir -p /analyze/temp'], shell=True, check=True)
        with open('/analyze/sequence.fasta', 'w') as out:
            out.write(f'>JOBID = {this_uuid}\n')
            out.write(f'{sequence}\n')
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

        rd.hset(this_uuid, 'result', json.dumps(result))
        return result


api.add_resource(RunTest, '/')
api.add_resource(RunJob, '/job')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
