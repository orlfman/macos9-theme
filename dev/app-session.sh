#!/bin/bash
# Runs inside the nested KWin started by app-test.sh: starts the app in
# $M9_APP, waits $M9_WAIT seconds, screenshots the virtual screen into
# $M9_OUT, then exits, which ends the nested KWin.
eval "$M9_APP" &
sleep "${M9_WAIT:-6}"
spectacle -b -n -f -o "$M9_OUT"
sleep 1
kill $(jobs -p) 2> /dev/null
