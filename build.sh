#!/usr/bin/env bash
cd "$(dirname "$0")"

echo "building docker image: tracker"
docker build -t tracker -f dockerfile .

if [ $? -eq 0 ]; then
    echo "build succeeded. run it with:"
    echo "  docker run --rm -it --device=/dev/video0 tracker"
else
    echo "build failed"
    exit 1
fi