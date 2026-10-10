# dev-reaper

Stops leftover developer processes on macOS that hold memory and file watchers after
the session that started them is gone, and reports the ones it should not touch.

It targets the leftovers of AI coding agents and multi-worktree workflows: idle Nx
daemons, MCP servers, tsserver and Biome LSP processes, Playwright daemons and browsers,
and wedged dev servers. It is a single Python 3 script with no dependencies, meant to
run from a LaunchAgent every 30 minutes.

## What it does

A process is judged idle by its cumulative CPU time over a short sampling window
(5 s by default), not by the `%CPU` column. Only the current user's processes are
considered.

Stopped (SIGTERM, then SIGKILL after a grace period):

- **Nx daemons** whose workspace is gone, or whose `daemon.log` shows no open client
  connection and no handled request for 60 minutes. A connected client such as
  Nx Console or `nx watch` keeps the daemon alive, and so does a missing or unreadable log.
- **Reparented helpers** (PPID 1, idle, older than 6 hours): MCP servers, tsserver,
  Biome LSP proxies, and Nx plugin workers.
- **Playwright CLI daemons and browsers** that are idle and older than 24 hours.
- **Wedged dev servers**: PPID 1, older than 2 hours, and busy both now and on average
  over their lifetime.

Reported only, with one macOS notification per new set: idle reparented dev servers,
idle `cursor-agent` processes older than 24 hours, and reparented `yarn install` runs.

## Usage

```sh
dev-reaper --dry-run    # print what it would stop or report; changes nothing
dev-reaper --mcp-only --dry-run  # preview only idle reparented MCP servers
dev-reaper              # act, and log to ~/Library/Logs/dev-reaper.log
```

`--json` changes only the output format. Without `--dry-run` it still acts, so
combine the two flags to preview decisions as JSON.

`--mcp-only` selects only idle reparented MCP servers older than `--orphan-hours`
(6 hours by default). It skips the Nx, LSP, browser, dev-server, and report rules.
The CLI retains all existing rules when the flag is absent. For MCP-only scheduled
cleanup, add `<string>--mcp-only</string>` after the script path in the LaunchAgent.

Thresholds are flags; see `dev-reaper --help`.

## Install

```sh
install -m 755 dev-reaper ~/.local/bin/dev-reaper
dev-reaper --dry-run
```

To run it every 30 minutes, copy `launchd/dev-reaper.plist.example` to
`~/Library/LaunchAgents/local.dev-reaper.plist`, replace `/Users/YOU` with your
home directory, and load it:

```sh
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/local.dev-reaper.plist
```

## Tests

```sh
python3 tests/smoke.py
```

The smoke test feeds recorded `ps` snapshots to the script and checks its decisions.
It sends no signals.

## License

[MIT](LICENSE)
