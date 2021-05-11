#!/bin/bash
SERVER_IP='miners-node'
SERVER_PORT=40000
HASH="QUERY_MINER $1"

SUCCESS_MSG='== Server responded successfully'
ERROR_MSG='XX Response failed!'

docker build -f ping.Dockerfile -t nc-ubuntu .
docker run -i --network=fiuba-dist1-tp1_testing_net nc-ubuntu sh -c "\
    echo $HASH | \
    nc $SERVER_IP $SERVER_PORT" | \
    (read RESPONSE;\
    echo $RESPONSE;\
    if [[ "$RESPONSE" =~ .*"STATS_MINERID_TOTAL_SUCCESS".* ]];\
        then echo $SUCCESS_MSG;\
    else echo $ERROR_MSG;\
    fi)
