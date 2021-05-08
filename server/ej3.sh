#!/bin/bash
SERVER_IP='server'
SERVER_PORT=12345
MESSAGE='hi!'$RANDOM

SUCCESS_MSG='== Server responded successfully'
ERROR_MSG='XX Response failed!'

docker build -f ej3.Dockerfile -t nc-ubuntu .
docker run -i --network=fiuba-dist1-tp0_testing_net nc-ubuntu sh -c "\
    echo $MESSAGE | \
    nc $SERVER_IP $SERVER_PORT" | \
    (read RESPONSE;\
    if [[ "$RESPONSE" =~ .*"$MESSAGE".* ]];\
        then echo $SUCCESS_MSG;\
    else echo $ERROR_MSG;\
    fi)
