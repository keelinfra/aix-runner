# Installing aix-runner

The short version is in the [README](../README.md#install). This page covers the rest.

## Run in the background

To keep the runner going after you log out:

```sh
nohup ./gitlab-runner run --config "$HOME/gitlab-runner/config.toml" \
  --working-directory "$HOME/gitlab-runner" > "$HOME/gitlab-runner/runner.log" 2>&1 &
```

Stop it with `kill -QUIT <pid>`: it waits for running jobs to finish, and exits within a second when idle. `gitlab-runner install` (running it as a system service) hasn't been tested on AIX yet.

## Check where a binary came from

Each release has a `sha256sums.txt`, and the Release workflow records build provenance for the binary. On a machine with the GitHub CLI:

```sh
gh attestation verify gitlab-runner-aix-ppc64 --repo keelinfra/aix-runner
```

## Build it yourself

On Linux or macOS with Go and git installed:

```sh
./build.sh v19.5.1      # output: dist/gitlab-runner-aix-ppc64
```

How the build works: [how-it-works.md](how-it-works.md).
