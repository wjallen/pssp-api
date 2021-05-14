## PSSP API

This is a demo repository for the COE332 class on how to build a REST API interface to a
scientific code base. The example code used here is a protein secondary structure
prediction (PSSP) tool called *Predict_Property*: https://github.com/realbigws/Predict_Property

There are three containerized components:

1) A Flask API front end for submitting / accessing jobs
2) A Redis database for storing job information
3) A worker back-end which runs the PSSP code


### Flask API Front End

The API front end is exposed on port 5000 inside the container, and mapped to port
5041 on ISP. Try, for example, the following routes:

```
$ curl localhost:5000/

/                 informational            
/run              (GET) job instructions   
/run              (POST) submit job        
/jobs             get list of past jobs    
/jobs/<UUID>      get job results          
/download/<UUID>  download img from job    
/delete           (GET) delete instructions
/delete           (DELETE) delete job      

```

The `/run` route will print instructions if sent a GET request, and if sent a POST
request will create and submit jobs, which looks like:

```
$ curl -X POST -d "seq=AAAAA" localhost:5000/run
Job a62467d2-605e-4bc2-abf5-6cd0b72041cd submitted to the queue
```

In that case, the sequence "AAAAA" is analyzed. To see a list of all jobs, hit
the `/jobs` route with a GET request:

```
$ curl localhost:5000/jobs
{
    "a62467d2-605e-4bc2-abf5-6cd0b72041cd": {
        "datetime": "2021-05-13 11:50:25.218075",
        "status": "finished"
    }
```

And curl the status / output of a specific job by providing the UUID in the URL:

```
$ curl localhost:5000/jobs/a62467d2-605e-4bc2-abf5-6cd0b72041cd
{
    "datetime": "2021-05-13 11:50:25.218075",
    "status": "submitted",
    "result": "pending",
    "input": "AAAAA"
}
```

When the job completes, the result will be updated and an image (plot) will also
be added. Download the image using the following route, making sure to redirect
the output to file:

```
$ curl localhost:5000/download/a62467d2-605e-4bc2-abf5-6cd0b72041cd > output.png
```

Finally, you can delete a specific job using the `/delete` route. A GET request
will provide instructions, and a DELETE request along with the JOBID will permanently
delete the job from the database:

```
$ curl -X DELETE -d "jobid=a62467d2-605e-4bc2-abf5-6cd0b72041cd" localhost:5000/delete
Job a62467d2-605e-4bc2-abf5-6cd0b72041cd deleted
$ curl -X DELETE -d "jobid=all" localhost:5000/delete
Job all deleted
```

To build and run a new copy of the API container on ISP for testing, use the 
following commands:

```
make clean-api     # remove api container
make test-api      # build dockerfile and start api container
```


### Redis DB

The Redis db uses the stock Docker image redis/6.2.3. It mounts the local /data
folder inside the container when doing `docker run` on ISP. The database is dumped
every so often to /data/dump.rdb. It will automatically be reloaded if the container
goes down and back up.

The container uses the default Redis port inside the container (6379), and is
mapped to 6441 on ISP. To start a new container on ISP, do:

```
make clean-db     # remove db container
make test-db      # build dockerfile and start db container
```

Here are some useful commands for testing:

```
[isp02]$ redis-cli -p 6441
<127.0.0.1:6441> KEYS *
1) "43d53284-1039-481e-a1f9-fb16c63fddbf" 
2) "0539aa84-e8ab-4ffd-9c78-8cc21660e2e7" 
```


### Worker - Executes Predict_Property

The scientific code for predicting properties is found here:

https://github.com/realbigws/Predict_Property

The expected input is a primary protein sequence of any length. A schematic
example of the results is shown below:
```
>original description
ASDFASDGFAGASG    #-> user input sequence with invalid amino acid shown as 'X'.
HHHHEEECCCCCHH    #-> 3-class secondary structure (SS3) prediction.
HHGGEEELLSSTHH    #-> 8-class secondary structure (SS8) prediction.
EEMMEEBBEEEBBM    #-> 3-state solvent accessibility (ACC) prediction.
*****......***    #-> disorder (DISO) prediction, with disorder residue shown as '*'.
_____HHHHH____    #-> 2-class transmembrane topology (TM2) prediction.               
UU___HHHHH____    #-> 8-class transmembrane topology (TM8) prediction.               

For 3-state secondary structure (SS3), H, E, and C represent alpha-helix, beta-sheet and coil, respectively.

For 8-state secondary structure (SS8), H, G, I, E, B, T, S, and L represent alpha-helix, 3-helix, 5-helix (pi-helix), extended strand in beta-ladder, isolated beta-bridge, hydrogen bonded turn, bend, and loop, respectively.

The relevant solvent accessibility is divided into three states by 2 cutoff values: 10% and 40% so that the three states have equal distribution. Buried for less than 10%, exposed for larger than 40% and medium for between 10% and 40%. Buried, Medium and Exposed are also abbreviated as B, M and E, respectively.
```

If running the tool on the command line, a `head -n 8 <id>PROP/<id>.all` will
return all of the useful lines. Here are some commands to deploy a test worker
container on ISP:

```
make clean-wrk    # remove worker container
make test-wrk     # build dockerfile and start worker container
```

Since the worker is just waiting to consume jobs from the hotqueue, the best way
to test is actually submitting jobs to the API and not calling this code directly.


### Docker Bridge Network

The Makefile assumes that there is a bridge network called:
`${NSPACE}-network-test`, where ${NSPACE} is something unique, like your
username, as defined in the top of the Makefile. To create it, do, e.g.:

```
docker network create wallen-network-test
```


### Docker Compose

The above commands are useful for launching and testing individual parts of
the app. Docker-compose targets have also been written into the Makefile to
test orchestration of all components as a unit. Before doing this, though, it
is a good idea to clean up all of the test containers:

```
make clean-all 
```

The following will build the version of containers specified in the top of the
Makefile as 'VER', and it will launch each of the three services one by one.

```
make compose-up
```

To tear down all three services:

```
make compose-down
```


### Tag Release

A Github - Dockerhub integration is set up so that every time a new release is
tagged in the git repo, the API and worker containers will automatically re-build
and tag themselves with the same release tag (even if there are no changes to
the dockerfiles or source code). To tag a release, follow these general steps:

```
#
# make some changes to code, test and confirm it is working
#

vim Makefile             # increment the VER at the top of the Makefile
git add .                # add all the new code
git commit -m 'message'  # commit changes
git push                 # push to github

git tag -a <tag> -m 'msg'  # add a new tag with descriptive 'msg'
git push origin <tag>      # push the tag up to github
```

The last 'git push' will have the downstream effect of triggering a re-build
of both images on Dockerhub. That can take 5-10 minutes. Once the new tags
are all seen on Dockerhub, delete the local containers (`make clean-all`) and
try to re-orchestrate all of them with:

```
make compose-up
```

To determine the appropriate version, try to follow these general guidelines:

1. (patch) increment the last digit (0.0.X) for bugfixes
2. (minor) increment the middle digit (0.X.0) for new features that are backwards compatible
3. (major) increment the first digit (X.0.0) for major changes that are not backwards compatible

See: https://semver.org/



### Kubernetes

Currently supporting a Kubernetes test and prod environment. The yaml files have a
few variables in them for image version and the Redis Service IP. The Redis Service 
IP is automatically grabbed as part of the make target. The only change needed is
to specify the desired Docker image tag in the top of the Makefile. Once that is
set, you can do this to launch everything:

```
make k-test    # launch test / staging env
make k-prod    # launch prod env
```

The services can be torn down with:

```
make k-test-del
make k-prod-del
```



### Testing

A simple functional test is included. If testing on ISP, you first have to pip
install the pytest library, then in the top directory of this repo execute:

```
pytest
```

The big test in there will actually run a job, check the result, and delete the job
that it ran. The test script should grab the appropriate Flask port from the Makefile.
Tesing should work the same on ISP and inside the Flask API pod on kubernetes.
