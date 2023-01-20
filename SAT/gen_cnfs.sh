#!/bin/bash
# SHEBANG

t="$1"
n="$2"
c="$3"
k="$4"

cd "$(dirname $0)"

python src/random_cnf.py "$t" "$n" "$c" "$k" || exit 1