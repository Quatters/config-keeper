# config-keeper

[![CI](https://github.com/Quatters/config-keeper/actions/workflows/ci.yml/badge.svg?event=push)](https://github.com/Quatters/config-keeper/actions/workflows/ci.yml)
![Codecov](https://img.shields.io/codecov/c/github/Quatters/config-keeper)
![PyPI - Version](https://img.shields.io/pypi/v/config-keeper2)
![PyPI - Downloads](https://img.shields.io/pypi/dm/config-keeper2)

User-friendly CLI for keeping your personal files or directories in
a repository.

In a few words **config-keeper** does following:

* Collects information about what files on current machine it should keep
* Makes a temporary copy of all these files and pushes it to specified
repository
* Pulls files from a repository later and puts them to the right places

# Table of contents

* [Use cases](#use-cases)
* [Key features](#key-features)
* [Install](#install)
  * [Using pipx (recommended)](#using-pipx-recommended)
  * [Using pip](#using-pip)
* [Usage](#usage)
  * [Quick start](#quick-start)
  * [Autocompletion](#autocompletion)
  * [CLI Reference](#cli-reference)

## Use cases

1. You spend a lot of time writing launch/build tasks or making config files
for a project you develop, but these stuff cannot be placed along with the
project itself.
1. You have to switch between work computers from time to time while you
working on same project and you have to send yourself archives with
bunch of updated files.
1. You want to save some system-wide config (like .bashrc) to use
it later or quickly restore if something goes wrong.

Finally, you want to **automate** these stuff.

## Key features

* Create projects as logical groups of files to sync and a repository
* All configuration in a single YAML file - update it using CLI or by hands
using ``validate`` command after
* Terminal auto-completion
* User-friendly error messages if something goes wrong

## Install

### Using pipx (recommended)

[Install ``pipx``](https://pypa.github.io/pipx/installation/) first.

```shell
pipx install config-keeper2
```

### Using pip

```shell
pip install --user config-keeper2
```

**NOTE**: if you are using latest versions of Ubuntu/Debian/Fedora, you may
also need to use `--break-system-packages` flag. Refer to
[PEP 668](https://peps.python.org/pep-0668/) for more information.

## Usage

``config-keeper`` relies on a **project** as logical group of files to sync
and a repository. Each project consists of

- **Paths**. These are any files or directories in your filesystem which you
want to keep. Some of them might not exist yet, if you are want to pull them
first from existing repository. But they must exist if you are going to push.
- **Repository**. Here your files and directories live. When you going to push
or pull, this repository is used.
- **Branch**. The branch of repository. Nothing special. If you want, you can
use the same repository across multiple projects with different branches.

### Quick start

To begin, create a project:

```shell
config-keeper project create myproject
# Repository: git@github.com:MyUser/personal-stuff.git
# Branch [main]: mybranch
# Project "myproject" saved.
```

Here assumed that repository exists and you have permissions
to communicate with it. Branch may exist or not - if not, it will be created
at first push.

Next, add path to the project:

```shell
config-keeper paths add \
    --project myproject \
    my_config.ini:~/configs/my_config.ini \
# Project "myproject" saved.
```

Here we said that ``~/configs/my_config.ini`` file should live in our
repository as ``my_config.ini``.

Assuming that ``~/configs/my_config.ini`` exists, let's push it:

```shell
config-keeper push myproject
# Going to push into following branches:
# - "mybranch" at git@github.com:MyUser/personal-stuff.git (from "myproject")
# Proceed? [Y/n]:
```

If something goes wrong at this step (or at any other step) you will probably
have a nice-readable error. If this is not your case please create an
[issue](https://github.com/Quatters/config-keeper/issues) describing how
to reproduce the bug and the desired behavior.

Now, if you visit repository, you should see that ``mybranch`` has recent
commit with ``my_config.ini`` file.

Finally, imagine you want to restore ``my_config.ini`` on your local machine
from a repository. All you need to do is

```shell
config-keeper pull myproject
# Following paths will most likely be replaced:
# - /home/<my_user>/configs/my_config.ini (from "myproject")
# Proceed? [Y/n]:
```

If you confirmed replacing, the ``~/configs/my_config.ini`` file now should
be the same as in repository one.

### Autocompletion

Run

```shell
config-keeper --install-completion
```

and reload shell.

**NOTE**: there is a
[known issue](https://github.com/tiangolo/typer/issues/54#issue-574856032) with
`zsh`. As a workaround you can add `compinit -D` to the end of your `.zshrc`
after installing completion.

### CLI Reference

To learn what commands are available, please refer to
[REFERENCE](./REFERENCE.md).

**NOTE**: you can always check the description of any command by using
``--help``, e.g.

```shell
config-keeper push --help
```
