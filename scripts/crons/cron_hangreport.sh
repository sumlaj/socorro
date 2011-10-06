#!/bin/bash

. /etc/socorro/socorrorc

NAME=`basename $0 .sh`
lock $NAME
pyjob $NAME startHangReport
EXIT_CODE=$?
unlock $NAME

exit $EXIT_CODE