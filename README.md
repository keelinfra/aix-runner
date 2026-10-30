<a href="https://keelinfra.io">
  <picture>
    <source media="(prefers-color-scheme: dark)"
            srcset="https://raw.githubusercontent.com/keelinfra/.github/main/assets/wordmark-dark.svg">
    <img alt="keelinfra" width="280"
         src="https://raw.githubusercontent.com/keelinfra/.github/main/assets/wordmark-light.svg">
  </picture>
</a>

# AIX Runner for GitLab

[![Build](https://github.com/keelinfra/aix-runner/actions/workflows/build.yml/badge.svg)](https://github.com/keelinfra/aix-runner/actions/workflows/build.yml)
[![Release](https://img.shields.io/github/v/release/keelinfra/aix-runner)](https://github.com/keelinfra/aix-runner/releases/latest)
[![AIX](https://img.shields.io/badge/AIX-7.2%20%7C%207.3-blue)](#status)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license)

Run **GitLab Runner on AIX 7.2 and 7.3** (ppc64), built from the unmodified upstream release.

> aix-runner is an independent project. It is not part of, or endorsed or supported by, GitLab. Please report problems [here](https://github.com/keelinfra/aix-runner/issues), not to GitLab's issue tracker.

**Why.** GitLab doesn't ship the runner for AIX, and AIX support is [not on its roadmap](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/6324). The runner itself builds for AIX; four of its dependencies don't. aix-runner patches those dependencies and publishes the binary, so an AIX host can run GitLab CI jobs with the shell executor like any other runner.

## How it works

1. [`build.sh`](build.sh) takes the upstream gitlab-runner tag; the runner's own code is not changed.
2. [`patch_deps.py`](patch_deps.py) patches four dependencies that don't compile for AIX.
3. Go cross-compiles it with `GOOS=aix GOARCH=ppc64 CGO_ENABLED=0`. A daily CI build of the latest upstream tag catches upstream changes early.

Details: [docs/how-it-works.md](docs/how-it-works.md).

## Status

Experimental and free to use. CI on Linux builds the latest upstream release every day; runs on AIX are tested by hand, not in CI.

| Platform | Status |
|---|---|
| AIX 7.3, shell executor | Tested with 19.5.1 against gitlab.com: register, jobs, artifacts, local cache, git clone, cancel; not in CI |
| AIX 7.2 | Not tested yet; same binary, should work |
| AIX 7.1 and older | Not supported: Go requires AIX 7.2 |
| Docker and Kubernetes executors | Not applicable on AIX |

Running Jenkins agents on AIX 7.1, Solaris or HP-UX instead? See [Agent8](https://github.com/keelinfra/agent8).

## Install

On the AIX host (POWER8 or newer), with `git` and `bash` from the [AIX Toolbox](https://www.ibm.com/support/pages/aix-toolbox-open-source-software-overview). Download `gitlab-runner-aix-ppc64` and `sha256sums.txt` from the [latest release](https://github.com/keelinfra/aix-runner/releases/latest); AIX has no curl or wget by default, so download them elsewhere and `scp` them over, or use curl from the Toolbox. Create the runner and its token in GitLab first (Settings > CI/CD > Runners).

```sh
sha256sum -c sha256sums.txt          # or: openssl dgst -sha256 gitlab-runner-aix-ppc64
mv gitlab-runner-aix-ppc64 gitlab-runner && chmod +x gitlab-runner
mkdir -p "$HOME/gitlab-runner"

./gitlab-runner register --non-interactive \
  --config "$HOME/gitlab-runner/config.toml" \
  --url https://gitlab.example.com --token "$RUNNER_TOKEN" \
  --executor shell --env "PATH=/opt/freeware/bin:/usr/bin:/bin"
./gitlab-runner run --config "$HOME/gitlab-runner/config.toml" \
  --working-directory "$HOME/gitlab-runner"
```

Keep the `--env PATH=...` line: the Toolbox installs git and bash under `/opt/freeware/bin`, and jobs fail to clone without it. Use an absolute `--config` path, because the runner reloads the file from that path.

More in [docs/install.md](docs/install.md): running in the background, checking where a binary came from, and building it yourself.

## Known gaps

- Cancelling a job takes about 20 seconds: the runner learns about the cancel at its next status update for the job. The job's processes are then killed.
- Not tested yet: AIX 7.2, `gitlab-runner install` as a system service, distributed (S3/GCS) cache, long-running stability.
- The binary is about 150 MB, because the Docker and Kubernetes executors are compiled in even though they have nothing to talk to on AIX.

When you report a problem, include `oslevel -s`, `./gitlab-runner --version` and the relevant lines of the runner log.

## Support

aix-runner is free and stays MIT. Bugs go to [issues](https://github.com/keelinfra/aix-runner/issues). If you need paid support for running it on your AIX hosts, email [hello@keelinfra.io](mailto:hello@keelinfra.io).

## License

[MIT](LICENSE), like GitLab Runner itself.

This product is based on GitLab software. GitLab is a trademark of GitLab Inc. This project is not affiliated with or endorsed by GitLab Inc.
