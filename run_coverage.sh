#!/usr/bin/env bash
# Run pytest with coverage and show a report
export TEST_DB_USER="yamlo_user"
export MY_TEST_VAR="yamlo_env"
export TEST_DB_PASS="yamlo_pass"
coverage run -m pytest -s "$@"
coverage report -m
coverage html

echo "\nHTML coverage report generated at htmlcov/index.html"
