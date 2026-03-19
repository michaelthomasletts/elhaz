<p align="center">
  <img 
    src="https://raw.githubusercontent.com/michaelthomasletts/assume-cli/refs/heads/main/docs/_static/transparent_header.png" 
    alt="assume" 
  />
</p>

<p align="center">
  <img 
    src="https://raw.githubusercontent.com/michaelthomasletts/assume-cli/refs/heads/main/docs/_static/transparent_header_assume.png" 
    alt="assume" 
  />
</p>

**ASSUME IS ACTIVELY UNDER DEVELOPMENT AND NOT YET READY FOR OFFICIAL RELEASE**

## Description

`assume` is a CLI tool with a daemon for exposing automatically refreshed temporary AWS credentials via [boto3-refresh-session](https://github.com/61418/boto3-refresh-session) to shells, SDKs, tools, and more. assume uses a UNIX domain socket with an in-memory session cache and a simple refresh loop.

## Installation

For beta testing, install `assume` into a dedicated virtual environment from a local clone of this repository.

```bash
git clone https://github.com/michaelthomasletts/assume-cli.git
cd assume-cli

uv venv
source .venv/bin/activate
uv sync
```

`uv sync` installs the project dependencies and installs the `assume` CLI into the active virtual environment, so you can run:

```bash
assume --help
```

If you need to resync after pulling updates from the beta branch, run:

```bash
uv sync
```

## Commands

```
% assume --help

 Usage: assume [OPTIONS] COMMAND [ARGS]...                                                                                                                                                                
                                                                                                                                                                                                          
 Manage refreshable AWS credentials via a local daemon.                                                                                                                                                   
                                                                                                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config-dir                   -cd        PATH     Config directory. Default: ~/.assume/configs                                                                                      │
│ --config-file-extension        -cfe       TEXT     Config file extension. Default: .yaml                                                                                                               │
│ --socket-path                  -sp        PATH     UNIX socket path for daemon communication.                                                                                                          │
│ --logging-path                 -lp        PATH     Daemon log file path. Default: ~/.assume/logs/daemon.log                                                                          │
│ --max-unix-socket-connections  -musc      INTEGER  Max pending socket connections.                                                                                                                     │
│ --install-completion                               Install completion for the current shell.                                                                                                           │
│ --show-completion                                  Show completion for the current shell, to copy it or customize the installation.                                                                    │
│ --help                                             Show this message and exit.                                                                                                                         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ export  Export credentials for the specified config.                                                                                                                                                   │
│ exec    Execute a one-off command with AWS credentials as env vars.                                                                                                                                    │
│ shell   Spawn an interactive shell with auto-refreshed AWS credentials.                                                                                                                                │
│ whoami  Return the STS caller identity for the specified config.                                                                                                                                       │
│ config  Manage assume configurations.                                                                                                                                                                  │
│ daemon  Manage the assume daemon.                                                                                                                                                                      │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```
% assume config --help

 Usage: assume config [OPTIONS] COMMAND [ARGS]...                                                                                                                                                         
                                                                                                                                                                                                          
 Manage assume configurations.                                                                                                                                                                            
                                                                                                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ add     Create a new config in the local config store.                                                                                                                                                 │
│ list    List all config names in the local config store.                                                                                                                                               │
│ get     Return config details as formatted JSON.                                                                                                                                                       │
│ update  Update a config interactively.                                                                                                                                                                 │
│ remove  Remove a config from the local config store.                                                                                                                                                   │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```
% assume daemon --help

 Usage: assume daemon [OPTIONS] COMMAND [ARGS]...                                                                                                                                                         
                                                                                                                                                                                                          
 Manage the assume daemon.                                                                                                                                                                                
                                                                                                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ start   Start the daemon in the background.                                                                                                                                                            │
│ stop    Stop the running daemon gracefully.                                                                                                                                                            │
│ kill    Forcefully stop the daemon (alias for ``stop``).                                                                                                                                               │
│ logs    Print daemon log output.                                                                                                                                                                       │
│ list    List all active sessions in the daemon's cache.                                                                                                                                                │
│ add     Initialize an AWS session and add it to the daemon's cache.                                                                                                                                    │
│ remove  Remove an active session from the daemon's cache.                                                                                                                                              │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
