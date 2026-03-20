#!/bin/bash
# start.sh
cd /root/image-processor
pkill -f "server.main" 2>/dev/null
sleep 1
nohup python3 -m server.main 50051 > server.log 2>&1 &
sleep 2
cat server.log
echo "PID: $!"
