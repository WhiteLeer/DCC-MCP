# Legacy launcher

This directory contains the older `Claude Code` launcher flow.

It is no longer the recommended startup path for this repository.

## Why it is legacy

The old launcher assumed:

- a Claude-specific plugin configuration
- a Claude-specific desktop startup workflow
- a host app that would start the MCP server after toggling plugin state

The current repository direction is different:

- `Codex` is the primary host
- MCP registration should happen in `C:/Users/wepie/.codex/config.toml`
- the GUI should attach to a server already started by `Codex`

## Current recommendation

Use the docs in the repo root instead:

- `../README.md`
- `../CODEX_SETUP.md`
- `../使用说明.md`

## Status of files here

These files are kept for migration reference only. They should not be used as the primary onboarding path for new users of the project.


