## PSSP API

This is a demo repository for the COE332 class on how to build a REST API interface to a
scientific code base. The example code used here is a protein secondary structure
prediction (PSSP) tool called *Predict_Property*: https://github.com/realbigws/Predict_Property

There are three containerized components:

1) A Flask API front end for submitting / accessing jobs
2) A Redis database for storing job information
3) A worker back-end which runs the PSSP code


#### Flask API Front End

Mapped to port 5041 on ISP. Try the following routes:

```
curl localhost:5041/             # general info
curl localhost:5041/run          # get instructions to submit a job
curl localhost:5041/jobs         # get past jobs
curl localhost:5041/jobs/JOBID   # get results for JOBID
```

The `/run` route also has a POST method for submitting jobs, which looks like:

```
curl -X POST -d "seq=AAAAA" localhost:5041/run
```

In that case, the sequence "AAAAA" is analyzed.

When testing things, it assumes docker bridge network `${NSPACE}-network-test` exists,
where ${NSPACE} is defined in the Makefile. Do the following to deploy individual services:

```
make clean-api     # remove api container
make test-api      # build dockerfile and start api container
```


#### Redis DB

The Redis db configuration is located at ./data/redis.conf. It is mounted
inside the container at /data/ when doing `docker run`. It is customized to have
a more frequent save interval and bind to 0.0.0.0. It uses the default Redis
port inside the container (6379), and is mapped to 6441 on ISP It uses the default Redis
port inside the container (6379), and is mapped to 6441 on ISP.

The database is dumped every 2 minutes (if there is a change) to the file
/data/dump.rdb, which is captured in this directory as ./data/dump.rdb. The
database will automatically load that data when the container starts up. To 
delete the database, first stop the container, then remove the dump.rdb file,
and finally start a new container. Some useful commands:

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


#### Worker - Executes Predict_Property

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
container:

```
make clean-wrk    # remove worker container
make test-wrk     # build dockerfile and start worker container
```

Since the worker is just waiting to consume jobs from the hotqueue, the best way
to test is actually submitting jobs to the API and not calling the code directly.


#### Docker Bridge Network

The Makefile assumes that there is a bridge network called:
`${NSPACE}-network-test`, where ${NSPACE} is something unique, like your
username, as defined in the top of the Makefile. To create it, do, e.g.:

```
docker network create wallen-network-test
```


#### Compose

The above commands are useful for launching and testing individual parts of
the app. Docker-compose targets have also been written into the Makefile to
test orchestration of all components as a unit. Before doing this, though, it
is a good idea to clean up all of the test containers:

```
make clean-all 
```

The following will pull the version of containers from Docker Hub that are
specified in the top of the Makefile as 'VER', and it will launch each of the
three services one by one. There is a slight (sleep 5) before launching the
worker because the worker will terminate with a failure if it cannot connect
to the redis db.

```
make compose-up
```

To tear down all three services:

```
make compose-down
```


#### Tag Release

A Github - Dockerhub integration is set up so that every time a new release is
tagged in the git repo, the three docker containers will automatically re-build
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
of all images on Dockerhub. That can take 5-10 minutes. Once the new tags
are all seen on Dockerhub, delete the local containers (`make clean-all`) and
try to re-orchestrate all of them with:

```
make compose-up
```

That should do a re-pull and deployment of the newest images using the tag in the 
top of the Makefile.

To determine the appropriate version, try to follow these general guidelines:

1. (patch) increment the last digit (0.0.X) for bugfixes
2. (minor) increment the middle digit (0.X.0) for new features that are backwards compatible
3. (major) increment the first digit (X.0.0) for major changes that are not backwards compatible

See: https://semver.org/

