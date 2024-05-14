#!/bin/sh
# Change to this directory
cd `echo $0 | sed -e 's/[^/]*$//'`
echo '=== autopep8'
autopep8 -i --aggressive ../hystfit/*.py

echo '=== test'
./test.py

echo '=== mypy'
mypy ../hystfit/*.py

echo '=== flake8'
flake8 --ignore=E501,W504 ../hystfit/hystfit.py
