#!/bin/bash

# NOTE:  this script requires a crossbar server to be started, using the script
# crossbar_for_test_pger.sh

# Other options available:
# --db ...... the db connection string -- defaults to local sqlite db;
#             on server, use 'postgresql://db_user@localhost:5432/pgerdb'
# --realm ... the "realm" to choose on crossbar
# --debug ... sets logging level to DEBUG -- default is False

python ../repo/pger.py --home 'pangalaxian_test'

