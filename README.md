# Jarvis — personal AI assistant

A phone-friendly Uzbek chat site with a Windows companion agent.

## Components

- `web/`: responsive chat website with voice input on supported mobile browsers.
- `server.py`: Railway API, OpenAI Responses API with web search, and queued desktop actions.
- `desktop/`: Windows companion. It connects to the Railway service and handles only the allowlisted actions requested by the website.

## Railway setup

Set these service variables in Railway:

- `OPENAI_API_KEY`: OpenAI API key (keep it private).
- `JARVIS_ACCESS_TOKEN`: private passcode for the website.
- `JARVIS_AGENT_KEY`: private key used by the Windows companion.

After changing variables, deploy the service. Website: https://web-production-2e76118f.up.railway.app/

## Windows companion

Download `JarvisAgent.exe` from the latest GitHub release. On first launch enter the Railway service URL and the value of `JARVIS_AGENT_KEY` from Railway Variables. The key is saved in Windows Credential Manager. Keep the agent running while you want to control the computer from the website.

Computer actions are restricted to opening HTTPS pages, launching a small allowlist of apps, typing text into the active window, and a limited set of keyboard shortcuts. Each website-requested action requires your approval before it is sent to the agent. The companion does not accept shell commands.
