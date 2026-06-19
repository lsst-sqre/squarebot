#!/bin/bash

# Update uv version references based on the frozen version from uv.lock.

# Bash "strict mode", to help catch problems and bugs in the shell script.
# Every bash script you write should include this. See
# http://redsymbol.net/articles/unofficial-bash-strict-mode/ for details.
set -euo pipefail

# Determine the current frozen uv version. squarebot pulls uv in via the
# ``nox`` group (``nox[uv]``); ``pre-commit-uv`` is intentionally omitted from
# the ``lint`` group on Python 3.14, so unlike other SQuaRE apps uv is not in
# the lint group here.
uv_version=$(uv export -q --no-hashes --only-group nox \
             | grep ^uv== | sed 's/.*=//')

# Replace the version in the env variables in GitHub Actions workflows.
for f in .github/workflows/*.yaml; do
    sed "s/UV_VERSION: .*/UV_VERSION: \"$uv_version\"/" "$f" >"$f.n"
    if ! cmp -s "$f" "${f}.n"; then
	echo "Updating UV_VERSION to $uv_version in $f"
	mv "${f}.n" "$f"
    else
        rm "${f}.n"
    fi
done

# Replace the version in any Dockerfiles.
for f in Dockerfile*; do
    sed "s/uv:[0-9][0-9.]*/uv:$uv_version/" "$f" >"${f}.n"
    if ! cmp -s "$f" "${f}.n"; then
        echo "Updating uv container version to $uv_version in $f"
	mv "${f}.n" "$f"
    else
        rm "${f}.n"
    fi
done
