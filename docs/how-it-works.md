# How aix-runner works

[`build.sh`](../build.sh) clones the upstream gitlab-runner tag, runs [`patch_deps.py`](../patch_deps.py) and cross-compiles with `GOOS=aix GOARCH=ppc64 CGO_ENABLED=0`. The runner's own code is not changed. The patched dependencies:

| Dependency | Problem on AIX | Change |
| --- | --- | --- |
| github.com/denisbrodbeck/machineid | no AIX implementation | read the system id from `uname -f` |
| github.com/moby/term | `TIOCSWINSZ` overflows `int` as a constant | convert at run time |
| github.com/go-git/go-billy/v5 | no `flock(2)` | use `fcntl` locks |
| github.com/go-git/go-git/v5 | AIX missing from build tags | add `aix` |

`patch_deps.py` stops with an error when a dependency changes upstream and a patch no longer applies. The daily [Build](../.github/workflows/build.yml) workflow builds the latest upstream tag to catch that early. Releases are published manually with the [Release](../.github/workflows/release.yml) workflow, which also records build provenance for the binary.
