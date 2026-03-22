<p align="center">
  <img 
    src="https://raw.githubusercontent.com/michaelthomasletts/elhaz/refs/heads/main/docs/_static/transparent_header.png" 
    alt="elhaz" 
  />
</p>

</br>

<div align="center">

  <a href="https://pypi.org/project/elhaz/">
    <img 
      src="https://img.shields.io/pypi/v/elhaz?color=7d8450&logo=python&label=Latest%20Version&labelColor=%23474749"
      alt="pypi_version"
    />
  </a>

  <a href="https://pypi.org/project/elhaz/">
    <img 
      src="https://img.shields.io/pypi/pyversions/elhaz?style=pypi&color=7d8450&logo=python&label=Compatible%20Python%20Versions&labelColor=%23474749" 
      alt="py_version"
    />
  </a>

  <a href="https://github.com/61418/elhaz/actions/workflows/push.yml">
    <img 
      src="https://img.shields.io/github/actions/workflow/status/61418/elhaz/push.yml?logo=github&color=7d8450&label=Build&labelColor=%23474749" 
      alt="workflow"
    />
  </a>

  <a href="https://github.com/61418/elhaz/commits/main">
    <img 
      src="https://img.shields.io/github/last-commit/61418/elhaz?logo=github&color=7d8450&label=Last%20Commit&labelColor=%23474749" 
      alt="last_commit"
    />
  </a>

  <a href="https://61418.io/elhaz">
    <img 
      src="https://img.shields.io/badge/Official%20Documentation-📘-7d8450?style=flat&labelColor=%23474749&logo=readthedocs" 
      alt="documentation"
    />
  </a>

  <a href="https://github.com/61418/elhaz">
    <img 
      src="https://img.shields.io/badge/Source%20Code-💻-7d8450?style=flat&labelColor=%23474749&logo=github" 
      alt="github"
    />
  </a>

  <a href="https://github.com/61418/elhaz/blob/main/LICENSE">
    <img 
      src="https://img.shields.io/static/v1?label=License&message=MPL-2.0&color=7d8450&labelColor=%23474749&logo=github&style=flat"
      alt="license"
    />
  </a>

<a href="https://pepy.tech/projects/elhaz">
  <img
    src="https://img.shields.io/endpoint?url=https%3A%2F%2Fmichaelthomasletts.github.io%2Fpepy-stats%2Felhaz.json&style=flat&logo=python&labelColor=%23474749&color=7d8450"
    alt="downloads"
  />
</a>  

</div>

</br>

<p align="center">
  <img 
    src="https://raw.githubusercontent.com/michaelthomasletts/elhaz/refs/heads/main/docs/_static/transparent_header_elhaz.png" 
    alt="elhaz" 
  />
</p>

</br>

## What is elhaz?

ᛉ elhaz ᛉ is a local AWS credential broker daemon exposed over a Unix socket.

Instead of a locally hosted HTTP metadata emulation service (ECS), which requires multiple processes for each assumed RoleArn, elhaz runs a single process (which accepts multiple concurrent connections) and serves automatically refreshed temporary AWS credentials on demand. 

It caches AWS sessions for however long the daemon is kept alive, which eliminates redundant session creations and STS calls. 

Unix-socket IPC is lightweight and gives a tighter local boundary than HTTP, avoids exposing local credential endpoints over TCP, and allows temporary credentials to live in memory rather than at rest on disk.

elhaz makes multi-role local AWS workflows cleaner by combining brokered access, in-memory caching, and host-local IPC in one model.

## Installation

With `uv`:

```bash
uv tool install elhaz
```

With `pipx`:

```bash
pipx install elhaz
```

## Usage

For general instructions on how to use elhaz, refer to the [quickstart guide](https://61418.io/elhaz/quickstart.html).

For technical information, refer to the [CLI documentation](https://61418.io/elhaz/cli/index.html) or run `elhaz --help` from your terminal. 

To learn critical concepts for properly using elhaz, refer to the [this page](https://61418.io/elhaz/concepts/index.html) of the official documentation.

## License

elhaz is licensed by the [Mozilla Public License 2.0 (MPL-2.0)](https://github.com/61418/elhaz/blob/main/LICENSE).

## Contributing

Refer to the [contributing guidelines](https://github.com/61418/elhaz?tab=contributing-ov-file).