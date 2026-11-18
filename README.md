# Jarvis — personal AI assistant

Personal assistant project for a phone-friendly web app and a Windows companion agent.

## Planned components

- `web/`: responsive chat interface for phone and desktop.
- `server/`: authenticated API, web search, and pairing between the web app and the user's Windows agent.
- `desktop/`: Windows companion, packaged as an `.exe` through GitHub Actions.

## Safety model

The desktop companion will only accept commands from a paired account and will ask for confirmation before actions that change files, send messages, install software, or otherwise have lasting effects. It will not expose an unrestricted remote shell.

## Deployment

The API is intended for Railway. Add provider credentials as Railway environment variables; never commit tokens or passwords. The website can be served by the API or deployed separately once hosting is connected.

## Status

Project scaffold is being prepared. Railway credentials and an AI provider key are required before a live assistant can answer requests. The Windows executable will be produced by the release workflow after the desktop component is implemented.
