#! /bin/bash

export DATASTORE_DATASET=forthsalon-hrd
export DATASTORE_EMULATOR_HOST=127.0.0.1:8099
export DATASTORE_EMULATOR_HOST_PATH=127.0.0.1:8099/datastore
export DATASTORE_HOST=http://127.0.0.1:8099
export DATASTORE_PROJECT_ID=forthsalon-hrd
env/bin/python3 main.py
