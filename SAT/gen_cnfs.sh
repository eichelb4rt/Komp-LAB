#!/bin/bash
# SHEBANG

t="$1"
n="$2"
c="$3"
k="$4"

cd "$(dirname $0)"

out_dir="random_cnfs"
if [ -d "$out_dir" ]; then rm -r "$out_dir"; fi

python src/random_cnf.py "$t" "$n" "$c" "$k" -o "$out_dir" || exit 1