#!/bin/bash
SERVER_IP='miners-node'
SERVER_PORT=40000

SUCCESS_MSG='== Server responded successfully'
ERROR_MSG='XX Response failed!'

# docker build -f ping.Dockerfile -t nc-ubuntu .
docker run -i --network=fiuba-dist1-tp1_testing_net nc-ubuntu sh -c '\
    for NUMERO in `seq 0 4`;\
    do echo QUERY_MINER $NUMERO | nc $1 $2; echo; done' "$MESSAGE" "$SERVER_IP" "$SERVER_PORT"
