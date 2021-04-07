## PSSP App

This is a demo repository for the COE332 class on how to build a REST API interface to a
scientific code base. The example code used here is a protein secondary structure
prediction (PSSP) tool called *Predict_Property*: https://github.com/realbigws/Predict_Property

There are three containerized components:

1) A Flask front end for submitting / accessing jobs
2) A Redis database for storing job information
3) A Flask-RESTful interface to the PSSP code


#### Flask Front End

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

When testing things, it assumes docker bridge network `wallen-network-test` exists.
Do the following to deploy individual services::

```
make clean-fe     # remove fe container
make test-fe      # build dockerfile and start fe container
```

The bridge network is not needed if doing `docker-compose up` - docker will make
one automatically.


#### Redis DB

The Redis db configuration is located at ./data/redis.conf. It is mounted
inside the container at /data/ when doing `docker run`. It is customized to have
a more frequent save interval and bind to 0.0.0.0.

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


#### API to Predict_Property

The scientific code for predicting properties is found here:

https://github.com/realbigws/Predict_Property

A schematic example of the results is shown below:
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
return all of the useful lines. Here are some commands to set up and test the
api container:

```
make clean-api    # remove api container
make test-api     # build dockerfile and start api container
```

Something like this can be used to test the api without going through the fe:

```
curl -H "Content-Type: application/json" \
     --request POST \
     --data '{"uuid":"this is my uuid","sequence":"CAPPCPAPCPAPAPCA"}' \
     localhost:5141/job
```


#### Docker Bridge Network

The Makefile assumes that there is a bridge network called:
`wallen-network-test`. If that doesn't exist, create it:

```
docker network create wallen-network-test
```

