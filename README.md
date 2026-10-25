# AIX Runner for GitLab

Unofficial builds of [GitLab Runner](https://gitlab.com/gitlab-org/gitlab-runner) for AIX 7.2 and 7.3 (ppc64).

GitLab doesn't ship the runner for AIX, and AIX support is [not on the roadmap](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/6324). The runner itself builds fine for AIX; a few of its dependencies don't. This repository patches those dependencies, builds the unmodified runner source for each upstream release, and publishes the binary.

> **Status: experimental.** Builds are produced by CI. Runtime testing on AIX is in progress; this section will list what has been tested.

## Requirements

- AIX 7.2 or 7.3 on POWER8 or newer. AIX 7.1 is not supported, because Go itself requires AIX 7.2.
- `git` and `bash` on the host, for example from the [AIX Toolbox](https://www.ibm.com/support/pages/aix-toolbox-open-source-software-overview).
- Only the **shell** executor makes sense on AIX. The Docker and Kubernetes executors are compiled in but have nothing to talk to.

## Install

```sh
# Pick a release from https://github.com/keelinfra/aix-runner/releases
# Download gitlab-runner-aix-ppc64 and sha256sums.txt from that release, then:
sha256sum -c sha256sums.txt          # or: openssl dgst -sha256 gitlab-runner-aix-ppc64
mv gitlab-runner-aix-ppc64 gitlab-runner && chmod +x gitlab-runner

./gitlab-runner register --non-interactive \
  --url https://gitlab.example.com \
  --token "$RUNNER_TOKEN" \
  --executor shell
./gitlab-runner run
```

Create the runner and its token in GitLab first (Settings > CI/CD > Runners). The release page also lists a `gh attestation verify` command to check that a binary came from this repository's workflow.

## How it's built

[`build.sh`](build.sh) clones the upstream tag, runs [`patch_deps.py`](patch_deps.py) and cross-compiles with `GOOS=aix GOARCH=ppc64 CGO_ENABLED=0`. The runner's own code is not changed. The patched dependencies:

| Dependency | Problem on AIX | Change |
| --- | --- | --- |
| github.com/denisbrodbeck/machineid | no AIX implementation | read the system id from `uname -f` |
| github.com/moby/term | `TIOCSWINSZ` overflows `int` as a constant | convert at run time |
| github.com/go-git/go-billy/v5 | no `flock(2)` | use `fcntl` locks |
| github.com/go-git/go-git/v5 | AIX missing from build tags | add `aix` |

`patch_deps.py` stops with an error when a dependency changes upstream and a patch no longer applies. The daily [Build](.github/workflows/build.yml) workflow builds the latest upstream tag to catch that early. Releases are published manually with the [Release](.github/workflows/release.yml) workflow.

Build it yourself on Linux or macOS with Go and git installed:

```sh
./build.sh v19.5.1      # output: dist/gitlab-runner-aix-ppc64
```

## Trademark

This product is based on GitLab software. GitLab is a trademark of GitLab Inc. This project is not affiliated with or endorsed by GitLab Inc. GitLab Runner is MIT-licensed; the scripts in this repository are MIT-licensed too ([LICENSE](LICENSE)).
