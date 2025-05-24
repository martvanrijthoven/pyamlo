#!/usr/bin/env bash
# Run pytest with coverage and show a report
coverage run -m pytest -s "$@"
coverage report -m
coverage html

echo "\nHTML coverage report generated at htmlcov/index.html"
