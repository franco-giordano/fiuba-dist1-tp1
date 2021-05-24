#!/bin/bash
SERVER_IP='miners-node'
SERVER_PORT=10000
MESSAGE='This is a test chunk!'

SUCCESS_MSG='== Server responded successfully'
ERROR_MSG='XX Response failed!'

# docker build -f ping.Dockerfile -t nc-ubuntu .
docker run -i --network=fiuba-dist1-tp1_testing_net nc-ubuntu sh -c '\
    for NUMERO in `seq 1 100`;\
    do echo $0 $NUMERO | nc $1 $2 & done; sleep 10' "$MESSAGE" "$SERVER_IP" "$SERVER_PORT"
