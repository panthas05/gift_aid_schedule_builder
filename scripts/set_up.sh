#!/bin/bash

cd $(dirname $0)
cd ../

# Setting up virtual environment
if [ ! -d "env" ]; then
    python3 -m venv env
fi
source env/bin/activate
python3 -m pip install -r requirements/base.txt

# creating base files
cp ./templates/transactions.csv ./transactions.csv
cp ./templates/declarations.csv ./declarations.csv

# creating outputs directory
mkdir outputs