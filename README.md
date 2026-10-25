# AIX Runner for GitLab

Unofficial builds of [GitLab Runner](https://gitlab.com/gitlab-org/gitlab-runner) for AIX 7.2 and 7.3 (ppc64).

GitLab doesn't ship the runner for AIX, and AIX support is [not on the roadmap](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/6324). The runner itself builds fine for AIX; a few of its dependencies don't. This repository patches those dependencies, builds the unmodified runner source for each upstream release, and publishes the binary.

> **Status: experimental.** Not affiliated with GitLab; no support beyond this repository's issues.

## Tested

GitLab Runner 19.5.1 on AIX 7.3 TL1 (7300-01-02), as a non-root user, shell executor, against gitlab.com (2026-10-25):

| Check | Result |
| --- | --- |
| Register with a runner authentication token | works |
| Shell job (bash 5.3 from the AIX Toolbox) | works |
| Artifacts upload | works |
| Local cache | works |
| Git clone (default fetch strategy, git 2.51 from the AIX Toolbox) | works |
| Cancel a running job | works: the job's foreground and background processes are killed. It took about 20 seconds after cancelling in the UI, because the runner only learns about the cancel at its next status update for the job. |
| Stop the runner (SIGQUIT) | exits within a second |

Not tested yet: AIX 7.2, `gitlab-runner install` as a system service, distributed (S3/GCS) cache, long-running stability.

## Requirements

- AIX 7.2 or 7.3 on POWER8 or newer. AIX 7.1 is not supported, because Go itself requires AIX 7.2.
- `git` and `bash` on the host, for example from the [AIX Toolbox](https://www.ibm.com/support/pages/aix-toolbox-open-source-software-overview).
- Only the **shell** executor makes sense on AIX. The Docker and Kubernetes executors are compiled in but have nothing to talk to.

## Install

```sh
# Pick a release from https://github.com/keelinfra/aix-runner/releases
# (before the first release: the artifact of the latest successful Build run)
# Download gitlab-runner-aix-ppc64 and sha256sums.txt from that release, then:
sha256sum -c sha256sums.txt          # or: openssl dgst -sha256 gitlab-runner-aix-ppc64
mv gitlab-runner-aix-ppc64 gitlab-runner && chmod +x gitlab-runner

mkdir -p "$HOME/gitlab-runner"
# Use absolute paths for --config: the runner reloads it later from that path.
./gitlab-runner register --non-interactive \
  --config "$HOME/gitlab-runner/config.toml" \
  --url https://gitlab.example.com \
  --token "$RUNNER_TOKEN" \
  --executor shell \
  --env "PATH=/opt/freeware/bin:/usr/bin:/bin"
./gitlab-runner run --config "$HOME/gitlab-runner/config.toml" \
  --working-directory "$HOME/gitlab-runner"
```

The `--env PATH=...` line matters: the AIX Toolbox installs git and bash under `/opt/freeware/bin`, which isn't on the default PATH, and jobs fail to clone without it.

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
