#!/usr/bin/env python3
"""Patch the gitlab-runner dependencies that don't build for AIX.

Run inside a gitlab-runner source tree after `go mod download`. Each dependency is
copied to _deps/<name>, edited in place, and wired in with `go mod edit -replace`.
Fails loudly when a dependency changed so much that a patch no longer applies:
check whether upstream fixed it and drop or update that patch.
"""
import json
import os
import shutil
import stat
import subprocess
import sys

DEPS_DIR = "_deps"


def go_module(path):
    out = subprocess.run(["go", "list", "-m", "-json", path],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def copy_module(path):
    mod = go_module(path)
    if not mod.get("Dir"):
        subprocess.run(["go", "mod", "download", path], check=True)
        mod = go_module(path)
    dest = os.path.join(DEPS_DIR, path.replace("/", "_"))
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(mod["Dir"], dest)
    for root, dirs, files in os.walk(dest):
        for name in dirs + files:
            p = os.path.join(root, name)
            os.chmod(p, os.stat(p).st_mode | stat.S_IWUSR)
    os.chmod(dest, os.stat(dest).st_mode | stat.S_IWUSR)
    return mod["Version"], dest


def replace_once(file, old, new):
    with open(file) as f:
        s = f.read()
    if s.count(old) != 1:
        sys.exit(f"patch no longer applies: {file}: expected one match of {old!r}")
    with open(file, "w") as f:
        f.write(s.replace(old, new))


def write(file, text):
    with open(file, "w") as f:
        f.write(text)


def machineid(d):
    # No AIX implementation; `uname -f` prints the system id.
    write(os.path.join(d, "id_aix.go"), '''//go:build aix

package machineid

import (
\t"os/exec"
\t"strings"
)

func machineID() (string, error) {
\tout, err := exec.Command("uname", "-f").Output()
\tif err != nil {
\t\treturn "", err
\t}
\treturn strings.TrimSpace(string(out)), nil
}
''')
    if not os.path.exists(os.path.join(d, "go.mod")):
        write(os.path.join(d, "go.mod"), "module github.com/denisbrodbeck/machineid\n\ngo 1.12\n")


def moby_term(d):
    # TIOCSWINSZ is 0xffffffff80087467 on AIX and overflows int as a constant.
    f = os.path.join(d, "term_unix.go")
    replace_once(f, "unix.IoctlSetWinsize(int(fd), unix.TIOCSWINSZ,",
                 "unix.IoctlSetWinsize(int(fd), tiocswinsz(),")
    with open(f, "a") as fh:
        fh.write("\n// tiocswinsz converts at run time; on AIX the constant doesn't fit in int.\n"
                 "func tiocswinsz() int { v := uint64(unix.TIOCSWINSZ); return int(v) }\n")


def go_billy(d):
    # AIX has no flock(2); use fcntl locks instead.
    f = os.path.join(d, "osfs", "os_posix.go")
    with open(f) as fh:
        s = fh.read()
    head = s.splitlines()[0]
    if not head.startswith("//go:build ") or "aix" in head:
        sys.exit(f"patch no longer applies: {f}: unexpected build line {head!r}")
    s = s.replace(head, head + " && !aix", 1)
    s = "\n".join(l for l in s.splitlines() if not l.startswith("// +build")) + "\n"
    write(f, s)
    aix = s.replace(head + " && !aix", "//go:build aix", 1)
    for old, new in [
        ("unix.Flock(int(f.File.Fd()), unix.LOCK_EX)",
         "unix.FcntlFlock(f.File.Fd(), unix.F_SETLKW, &unix.Flock_t{Type: unix.F_WRLCK})"),
        ("unix.Flock(int(f.File.Fd()), unix.LOCK_UN)",
         "unix.FcntlFlock(f.File.Fd(), unix.F_SETLK, &unix.Flock_t{Type: unix.F_UNLCK})"),
    ]:
        if aix.count(old) != 1:
            sys.exit(f"patch no longer applies: {f}: expected one match of {old!r}")
        aix = aix.replace(old, new)
    write(os.path.join(d, "osfs", "os_aix.go"), aix)


def go_git(d):
    # worktree_unix_other.go covers the other Unix systems; add aix to its build tags.
    f = os.path.join(d, "worktree_unix_other.go")
    with open(f) as fh:
        lines = fh.read().splitlines()
    out = []
    for l in lines:
        if l.startswith("//go:build "):
            l = l + " || aix"
        elif l.startswith("// +build "):
            l = l + " aix"
        out.append(l)
    if out == lines:
        sys.exit(f"patch no longer applies: {f}: no build line")
    write(f, "\n".join(out) + "\n")


PATCHES = [
    ("github.com/denisbrodbeck/machineid", machineid),
    ("github.com/moby/term", moby_term),
    ("github.com/go-git/go-billy/v5", go_billy),
    ("github.com/go-git/go-git/v5", go_git),
]


def main():
    os.makedirs(DEPS_DIR, exist_ok=True)
    for path, fn in PATCHES:
        version, dest = copy_module(path)
        fn(dest)
        subprocess.run(["go", "mod", "edit", f"-replace={path}=./{dest}"], check=True)
        print(f"patched {path} {version}")


if __name__ == "__main__":
    main()
