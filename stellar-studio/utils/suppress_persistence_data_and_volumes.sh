#!/bin/bash
#stellar-studio/utils/suppress_persistence_data_and_volumes.sh

docker compose down -v
wait

docker system prune -a --volumes
wait

sudo rm -rf data/mysql/
wait

mkdir -p data/mysql/
wait

sudo chown -R 999:999 data/mysql/
wait

sudo chmod -R 750 data/mysql/
