#!/bin/sh
# session hook script; write commands here to execute on the host at the
# specified state
BRIFNAME=$(find /sys/devices/virtual/net -name 'enp0s9' | awk -F '[/:]' '{print $6}')
ip addr add 10.0.0.254/24 dev $BRIFNAME
