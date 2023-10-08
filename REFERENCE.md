# `config-keeper`

**Usage**:

```console
$ config-keeper [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `config`
* `paths`
* `project`
* `pull`: Pull all files and directories of projects...
* `push`: Push files or directories of projects to...

## `config-keeper config`

**Usage**:

```console
$ config-keeper config [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `path`: Show configuration file path.
* `validate`: Validate config for missing or unknown...

### `config-keeper config path`

Show configuration file path.

**Usage**:

```console
$ config-keeper config path [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `config-keeper config validate`

Validate config for missing or unknown params, check repositories and paths.

**Usage**:

```console
$ config-keeper config validate [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `config-keeper paths`

**Usage**:

```console
$ config-keeper paths [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `add`: Add directories or files to project.
* `delete`: Delete paths by their keys from project.

### `config-keeper paths add`

Add directories or files to project. They will be pushed to (and pulled
from) repository.

**Usage**:

```console
$ config-keeper paths add [OPTIONS] PATHS...
```

**Arguments**:

* `PATHS...`: [required]

**Options**:

* `--project TEXT`: [required]
* `--overwrite / --no-overwrite`: [default: no-overwrite]
* `--help`: Show this message and exit.

### `config-keeper paths delete`

Delete paths by their keys from project. This will not affect original
files or directories.

**Usage**:

```console
$ config-keeper paths delete [OPTIONS] PATH_NAMES...
```

**Arguments**:

* `PATH_NAMES...`: [required]

**Options**:

* `--project TEXT`: [required]
* `--ignore-missing / --no-ignore-missing`: [default: no-ignore-missing]
* `--help`: Show this message and exit.

## `config-keeper project`

**Usage**:

```console
$ config-keeper project [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Create a new project.
* `delete`: Delete project.
* `list`: List all projects.
* `show`: Show project's config.
* `update`: Update project.

### `config-keeper project create`

Create a new project.

**Usage**:

```console
$ config-keeper project create [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `--repository TEXT`: [required]
* `--branch TEXT`: [default: main]
* `--check / --no-check`: [default: check]
* `--help`: Show this message and exit.

### `config-keeper project delete`

Delete project.

**Usage**:

```console
$ config-keeper project delete [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `--confirm / --no-confirm`: [default: confirm]
* `--help`: Show this message and exit.

### `config-keeper project list`

List all projects.

**Usage**:

```console
$ config-keeper project list [OPTIONS]
```

**Options**:

* `-v, --verbose`
* `--help`: Show this message and exit.

### `config-keeper project show`

Show project's config.

**Usage**:

```console
$ config-keeper project show [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `--help`: Show this message and exit.

### `config-keeper project update`

Update project.

**Usage**:

```console
$ config-keeper project update [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: [required]

**Options**:

* `--repository TEXT`
* `--branch TEXT`
* `--check / --no-check`: [default: check]
* `--help`: Show this message and exit.

## `config-keeper pull`

Pull all files and directories of projects from their repositories and move
them to projects' paths with complete overwrite of original files. This
operation is NOT atomic (i.e. failing operation for some project does not
prevent other projects to be processed).

**Usage**:

```console
$ config-keeper pull [OPTIONS] PROJECTS...
```

**Arguments**:

* `PROJECTS...`: [required]

**Options**:

* `--help`: Show this message and exit.

## `config-keeper push`

Push files or directories of projects to their repositories. This operation
is NOT atomic (i.e. failing operation for some project does not prevent
other projects to be processed).

**Usage**:

```console
$ config-keeper push [OPTIONS] PROJECTS...
```

**Arguments**:

* `PROJECTS...`: [required]

**Options**:

* `--help`: Show this message and exit.
