# `config-keeper`

CLI tool for keeping your personal config files in a repository

**Usage**:

```console
$ config-keeper [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--version`: Show current version and exit.
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `config`: Manage config of this tool.
* `paths`: Manage project paths.
* `project`: Manage projects.
* `pull`: Pull all files and directories of projects...
* `push`: Push files or directories of projects to...

## `config-keeper config`

Manage config of this tool.

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

Show configuration file path. You can set CONFIG_KEEPER_CONFIG_FILE
environment variable to change its path.

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

Manage project paths.

**Usage**:

```console
$ config-keeper paths [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `add`: Add directories or files to project.
* `delete`: Delete paths by their path names from...

### `config-keeper paths add`

Add directories or files to project. They will be pushed to (and pulled
from) repository.

**Usage**:

```console
$ config-keeper paths add [OPTIONS] PATHS...
```

**Arguments**:

* `PATHS...`: 
    Path list with following syntax: path_name:/path/to/file/or/dir. Path names
    of each project must be unique as it will be used as temporary file
    (directory) name for storing it in repository. Path after colon is any
    path to file (directory) in your filesystem.
  [required]

**Options**:

* `--project TEXT`: The name of project.  [required]
* `--overwrite / --no-overwrite`: If set, overwrite path names if project already has them. Fail otherwise.  [default: no-overwrite]
* `--help`: Show this message and exit.

### `config-keeper paths delete`

Delete paths by their path names from project. This will not affect original
files or directories.

**Usage**:

```console
$ config-keeper paths delete [OPTIONS] PATH_NAMES...
```

**Arguments**:

* `PATH_NAMES...`: 
    Path names of project.
  [required]

**Options**:

* `--project TEXT`: The name of project.  [required]
* `--ignore-missing / --no-ignore-missing`: If set, path names that are not exist in project will be ignored. Fail
otherwise.  [default: no-ignore-missing]
* `--help`: Show this message and exit.

## `config-keeper project`

Manage projects.

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
* `show`: Show project config.
* `update`: Update project.

### `config-keeper project create`

Create a new project.

**Usage**:

```console
$ config-keeper project create [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: 
    The name of project.
  [required]

**Options**:

* `--repository TEXT`: Repository which is used to store your files and directories.  [required]
* `--branch TEXT`: Branch of the repository used to push and pull from.  [default: main]
* `--check / --no-check`: Whether check if repository exist.  [default: check]
* `--help`: Show this message and exit.

### `config-keeper project delete`

Delete project.

**Usage**:

```console
$ config-keeper project delete [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: 
    The name of project.
  [required]

**Options**:

* `--confirm / --no-confirm`: Whether confirm before deleting.  [default: confirm]
* `--help`: Show this message and exit.

### `config-keeper project list`

List all projects.

**Usage**:

```console
$ config-keeper project list [OPTIONS]
```

**Options**:

* `-v, --verbose`: Show additional information.
* `--help`: Show this message and exit.

### `config-keeper project show`

Show project config.

**Usage**:

```console
$ config-keeper project show [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: 
    The name of project.
  [required]

**Options**:

* `--help`: Show this message and exit.

### `config-keeper project update`

Update project.

**Usage**:

```console
$ config-keeper project update [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: 
    The name of project.
  [required]

**Options**:

* `--repository TEXT`: Repository which is used to store your files and directories.
* `--branch TEXT`: Branch of the repository used to push and pull from.
* `--check / --no-check`: Whether check if repository exist.  [default: check]
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

* `--ask / --no-ask`: [default: ask]
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

* `--ask / --no-ask`: [default: ask]
* `--help`: Show this message and exit.
