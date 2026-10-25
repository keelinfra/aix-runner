#!/bin/sh
# Build GitLab Runner for AIX (ppc64) from an upstream release tag.
#
#   ./build.sh v19.5.1            # clones gitlab.com/gitlab-org/gitlab-runner at that tag
#   SRC=/path/to/checkout ./build.sh v19.5.1   # use an existing checkout instead
#
# Output: dist/gitlab-runner-aix-ppc64 and dist/sha256sums.txt
set -eu

TAG=${1:?usage: build.sh <gitlab-runner tag, e.g. v19.5.1>}
HERE=$(cd "$(dirname "$0")" && pwd)
DIST=${DIST:-$HERE/dist}
WORK=${WORK:-$HERE/work}

if [ -z "${SRC:-}" ]; then
  SRC=$WORK/gitlab-runner
  rm -rf "$SRC"
  git clone --quiet --depth 1 --branch "$TAG" https://gitlab.com/gitlab-org/gitlab-runner.git "$SRC"
fi
cd "$SRC"

REVISION=$(git rev-parse --short=8 HEAD 2>/dev/null || echo unknown)
VERSION=${TAG#v}
NS=gitlab.com/gitlab-org/gitlab-runner/common

python3 "$HERE/patch_deps.py"

mkdir -p "$DIST"
GOOS=aix GOARCH=ppc64 CGO_ENABLED=0 go build -trimpath \
  -ldflags "-X $NS.NAME=gitlab-runner -X $NS.VERSION=$VERSION -X $NS.REVISION=$REVISION -X $NS.BRANCH=$TAG -X $NS.BUILT=$(date -u +%Y-%m-%dT%H:%M:%S%z) -s -w" \
  -o "$DIST/gitlab-runner-aix-ppc64" .

cd "$DIST"
sha256sum gitlab-runner-aix-ppc64 > sha256sums.txt
cat sha256sums.txt
