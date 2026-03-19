<p align="center">
  <img 
    src="https://raw.githubusercontent.com/michaelthomasletts/elhaz/refs/heads/main/docs/_static/transparent_header.png" 
    alt="elhaz" 
  />
</p>

**ELHAZ IS ACTIVELY UNDER DEVELOPMENT AND NOT YET READY FOR OFFICIAL RELEASE**

**ACCORDINGLY, THIS REPOSITORY WILL CHANGE SUBSTANTIALLY UNTIL THE PROJECT REACHES A STABLE STATE AND IS OFFICIALLY RELEASED FOR USE**

## Description

Think of `elhaz` as your own local AWS STS.

`elhaz` is a CLI tool with a daemon for exposing automatically refreshed temporary AWS credentials via [boto3-refresh-session](https://github.com/61418/boto3-refresh-session) to shells, SDKs, tools, and more. elhaz uses a UNIX domain socket with an in-memory session cache and a simple refresh loop.

## Installation

For beta testing, install `elhaz` into a dedicated virtual environment from a local clone of this repository.

```bash
git clone https://github.com/michaelthomasletts/elhaz.git
cd elhaz

uv venv
source .venv/bin/activate
uv sync
```

`uv sync` installs the project dependencies and installs the `elhaz` CLI into the active virtual environment, so you can run:

```bash
elhaz --help
```

If you need to resync after pulling updates from the beta branch, run:

```bash
uv sync
```

## Quickstart

Create a config.

```bash
elhaz config add
```

`elhaz` will interactively help you create the config. The only required parameter is `RoleArn`. 

Next, start the daemon.

```bash
elhaz daemon start
```

Initialize the AWS session for your config.

```bash
elhaz daemon add -n <your config name>
```

Now the fun begins.

You can export your automatically refreshed temporary AWS credenitals to stdout.

```bash
elhaz export -n <your config name>
```

Or export env vars with those credentials:

```bash
elhaz export -n <your config name> -f env
```

Or execute a one-off AWS command using those credentials.

```bash
elhaz exec -n <your config name> --- aws s3 ls
```

Or initialize a shell and run as many AWS commands as you want, for however long you like.

```bash
elhaz shell -n <your config name>
```

If you have an existential crisis and forget who you are -- fret not, friend.

```bash
elhaz whoami -n <your config name>
```

You can also pass `elhaz` to `credential_process` in your AWS profile. So long as the `elhaz` daemon is running, `credential_process` will receive the credentials from stdout.

```
credential_process="elhaz export -n <your config name> -f credential-process"
```

With the daemon humming quietly in the background, you could also initialize a `Client` from a Python script and interact with the daemon that way _instead of using the CLI_.

```python
from elhaz.constants import Constants
from elhaz.daemon import Client

constants = Constants()

with Client(constants) as client:
    response = client.send("whoami", {"config": "my-config"})

if not response.ok:
    raise RuntimeError(response.error.message)

print(response.data)
```

## Commands

```
% elhaz --help

 Usage: elhaz [OPTIONS] COMMAND [ARGS]...                                                                                                                                                                
                                                                                                                                                                                                          
 Manage refreshable AWS credentials via a local daemon.                                                                                                                                                   
                                                                                                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config-dir                   -cd        PATH     Config directory. Default: ~/.elhaz/configs                                                                                      │
│ --config-file-extension        -cfe       TEXT     Config file extension. Default: .yaml                                                                                                               │
│ --socket-path                  -sp        PATH     UNIX socket path for daemon communication.                                                                                                          │
│ --logging-path                 -lp        PATH     Daemon log file path. Default: ~/.elhaz/logs/daemon.log                                                                          │
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
│ config  Manage elhaz configurations.                                                                                                                                                                   │
│ daemon  Manage the elhaz daemon.                                                                                                                                                                       │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```
% elhaz config --help

 Usage: elhaz config [OPTIONS] COMMAND [ARGS]...                                                                                                                                                         
                                                                                                                                                                                                          
 Manage elhaz configurations.                                                                                                                                                                            
                                                                                                                                                                                                          
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
% elhaz daemon --help

 Usage: elhaz daemon [OPTIONS] COMMAND [ARGS]...                                                                                                                                                         
                                                                                                                                                                                                          
 Manage the elhaz daemon.                                                                                                                                                                                
                                                                                                                                                                                                          
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
