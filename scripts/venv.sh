#!/bin/bash

# py -m venv venv 
# source .venv/bin/activate

# echo $VIRTUAL_ENV
# which python3
# which pip


pip install -r src/webapi/requirements.txt
pip install -r src/worker_app/requirements.txt
# pip install black isort pytest # Exemplo de pacotes de desenvolvimento