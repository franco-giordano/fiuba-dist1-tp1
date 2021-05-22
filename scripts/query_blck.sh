#!/bin/bash
SERVER_IP='blockchain-node'
SERVER_PORT=30000
HASH="QUERY_HASH $1"

SUCCESS_MSG='== Server responded successfully'
ERROR_MSG='XX Response failed!'

docker build -f ping.Dockerfile -t nc-ubuntu .
docker run -i --network=fiuba-dist1-tp1_testing_net nc-ubuntu sh -c "\
    echo $HASH | \
    nc $SERVER_IP $SERVER_PORT" | \
    (read RESPONSE;\
    echo $RESPONSE;\
    if [[ "$RESPONSE" =~ .*"BLOCK_HASH_FOUND".* ]];\
        then echo $SUCCESS_MSG;\
    else echo $ERROR_MSG;\
    fi)
