import pytest
import re
import requests
import time

flask_ip = 'localhost'
flask_port = '5041'
flask_prefix = f'http://{flask_ip}:{flask_port}'
test_UUID = ''


def test_top_info():

    route = f'{flask_prefix}/'
    response = requests.get(route)

    assert response.ok == True
    assert response.status_code == 200
    assert bool(re.search('Try these routes', response.text)) == True


def test_run_info():

    route = f'{flask_prefix}/run'
    response = requests.get(route)

    assert response.ok == True
    assert response.status_code == 200
    assert bool(re.search('POSTing sequences to run', response.text)) == True


def test_delete_info():

    route = f'{flask_prefix}/delete'
    response = requests.get(route)

    assert response.ok == True
    assert response.status_code == 200
    assert bool(re.search('DELETE-ing former jobs', response.text)) == True



def test_job():

    route_jobs = f'{flask_prefix}/jobs'
    response = requests.get(route_jobs)
    num_jobs_beg = len(response.json().keys()) 

    route_run = f'{flask_prefix}/run'
    run_data = {'seq': 'TESTTESTTEST'}
    response = requests.post(route_run, data=run_data)
    test_UUID = response.text.split()[1]
    assert response.ok == True
    assert response.status_code == 200
    assert bool(re.search('submitted to the queue', response.text)) == True

    route_jobs = f'{flask_prefix}/jobs'
    response = requests.get(route_jobs)
    assert response.ok == True
    assert response.status_code == 200
    assert isinstance(response.json(), dict) == True
    assert isinstance(response.json()[test_UUID], dict) == True
    assert len(response.json()[test_UUID].keys()) == 2
    assert isinstance(response.json()[test_UUID]['datetime'], str) == True
    assert isinstance(response.json()[test_UUID]['status'], str) == True
    assert response.json()[test_UUID]['status'] == 'submitted'

    time.sleep(15)
    route_job = f'{flask_prefix}/jobs/{test_UUID}'
    response = requests.get(route_job)
    assert response.ok == True
    assert response.status_code == 200
    assert isinstance(response.json(), dict) == True
    assert isinstance(response.json()['result'], dict) == True
    assert response.json()['result']['INP'] == 'TESTTESTTEST'
    assert response.json()['result']['SS3'] == 'CCCCCCCCCCCC'
    assert len(response.json()['result'].keys()) == 8
    assert isinstance(response.json()['datetime'], str) == True
    assert isinstance(response.json()['status'], str) == True
    assert response.json()['image'] == 'ready'
    assert response.json()['status'] == 'finished'

    route_download = f'{flask_prefix}/download/{test_UUID}'
    response = requests.get(route_download)
    assert response.ok == True
    assert response.status_code == 200
    assert isinstance(response.content, bytes) == True
    assert response.headers['Content-Type'] == 'image/png'

    route_del = f'{flask_prefix}/delete'
    del_data = {'jobid': test_UUID}
    response = requests.delete(route_del, data=del_data)
    assert response.ok == True
    assert response.status_code == 200
    assert bool(re.search('deleted', response.text)) == True

    route_jobs = f'{flask_prefix}/jobs'
    response = requests.get(route_jobs)
    num_jobs_end = len(response.json().keys()) 
    assert num_jobs_beg == num_jobs_end



