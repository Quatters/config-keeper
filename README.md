# config-keeper

User-friendly CLI for keeping your personal files or directories in
a repository.

In a few words **config-keeper** does following:

* Collects information about what files on current machine it should keep
* Makes a temporary copy of all these files and pushes it to specified
repository
* Pulls files from a repository later and puts them to the right places

Typical **use cases** are:

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
using ``validate`` command
* Terminal auto-completion
* User-friendly error messages if something goes wrong

## Install

### Using pip

```shell
pip install --user config-keeper2
```

**NOTE**:
if you are using latest versions of Ubuntu/Debian/Fedora, you may also
need to use `--break-system-packages` flag. Refer to
[PEP 668](https://peps.python.org/pep-0668/) for more information.

## Usage

Run

```shell
config-keeper --help
```

to see what commands are available.
