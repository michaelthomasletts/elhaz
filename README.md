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

**ASSUME IS ACTIVELY UNDER DEVELOPMENT**

## Description

assume is a CLI tool with a daemon for exposing automatically refreshed temporary AWS credentials via [boto3-refresh-session](https://github.com/61418/boto3-refresh-session) to shells, SDKs, tools, and more. assume uses a UNIX domain socket with an in-memory session cache and a simple refresh loop.