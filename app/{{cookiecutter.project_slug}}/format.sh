#!/usr/bin/env bash
set -x
set -e
black app tests
isort app tests --profile black
ruff check app tests --fix