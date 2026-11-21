#!/bin/bash
# Runs inside the nested KWin started by live-test.sh: starts the apps in
# $M9_APPS and waits until all of them are closed, which ends the nested
# KWin.
eval "$M9_APPS &"
wait
