#!/bin/bash

export CLIMODE="ON"
pipenv run python -m unittest discover -v tests -p "*.py"