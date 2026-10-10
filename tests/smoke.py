#!/usr/bin/env python3
"""Verify dev-reaper's stop/report decisions from injected ps snapshots; nothing is signalled."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dev-reaper"
NOW = 1_800_000_000.0
UID = 501
DAY, HOUR = "1-00:00:00", "01:00:00"


def iso(epoch):
    import datetime as dt
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


with tempfile.TemporaryDirectory(prefix="dev-reaper-smoke-") as tmp:
    tmp = Path(tmp)
    busy_ws, idle_ws, silent_ws = tmp / "busy", tmp / "idle", tmp / "silent"
    listener_ws, pnpm_ws = tmp / "listener", tmp / "pnpm"
    nx = "[NX v22.7.11 Daemon Server] - {} - {}\n"
    # workspace: (last handled request, open connections after it)
    for ws, last, open_after in ((busy_ws, NOW - 300, 0), (idle_ws, NOW - 7200, 0),
                                 (listener_ws, NOW - 7200, 1), (pnpm_ws, NOW - 60, 0)):
        log = ws / ".nx/workspace-data/d/daemon.log"
        log.parent.mkdir(parents=True)
        log.write_text(
            nx.format(iso(last - 1), "Established a connection. Number of open connections: 1")
            + nx.format(iso(last), "Handled json message GET_NX_CONSOLE_STATUS. Handling time: 1. Response time: 1.")
            + nx.format(iso(last + 1), f"Closed a connection. Number of open connections: {open_after}")
            + nx.format(iso(NOW - 600), "There are open file watchers or project graph listeners. Resetting inactivity timer.")
            + nx.format(iso(NOW - 10), "[REQUEST]: infra/cdk/x.ts")
        )
    silent_ws.mkdir()
    daemon = "/usr/bin/node {}/node_modules/nx/dist/src/daemon/server/start.js"
    pnpm_daemon = "/usr/bin/node {}/node_modules/.pnpm/nx@22.7.11/node_modules/nx/dist/src/daemon/server/start.js"

    # pid: (ppid, uid, etime, cputime before, cputime after, command)
    rows = {
        101: (1, UID, "2-00:00:00", "0:10.00", "0:10.00", daemon.format(tmp / "gone")),
        102: (1, UID, "2-00:00:00", "0:10.00", "0:10.00", daemon.format(busy_ws)),
        103: (1, UID, "2-00:00:00", "0:10.00", "0:12.00", daemon.format(idle_ws)),
        104: (1, UID, "30:00", "0:01.00", "0:01.00", daemon.format(silent_ws)),
        105: (1, UID, "03:00:00", "0:01.00", "0:01.00", daemon.format(silent_ws)),
        106: (1, UID, "2-00:00:00", "0:01.00", "0:01.00", daemon.format(listener_ws)),
        107: (1, UID, "2-00:00:00", "0:01.00", "0:01.00", pnpm_daemon.format(pnpm_ws)),
        108: (1, UID, "2-00:00:00", "0:01.00", "0:01.00", daemon.format("/Users/x/My Projects/ws")),
        109: (1, UID, "2-00:00:00", "0:01.00", "0:01.00", daemon.format(tmp / "gone" / "deeper")),
        201: (1, UID, "07:00:00", "0:01.00", "0:01.00", "/usr/bin/node /u/.npm/_npx/ab/node_modules/@playwright/mcp/cli.js"),
        202: (1, UID, "07:00:00", "0:01.00", "0:01.00", "/usr/bin/node /x/typescript/lib/tsserver.js"),
        206: (1, UID, "05:00:00", "0:01.00", "0:01.00", "/usr/bin/node /x/typescript/lib/tsserver.js"),
        203: (4242, UID, "9-00:00:00", "0:01.00", "0:01.00", "/usr/bin/node /x/npx/1password-mcp"),
        204: (1, UID, "16-01:00:00", "0:00.05", "0:00.05", "/x/@biomejs/cli-darwin-arm64/biome lsp-proxy --stdio"),
        205: (1, UID, "07:00:00", "0:01.00", "0:01.50", "/usr/bin/node /u/.npm/_npx/cd/node_modules/busy-mcp/cli.js"),
        301: (1, UID, "15-00:00:00", "0:02.00", "0:02.00", "/usr/bin/node /x/playwright-core/lib/entry/cliDaemon.js s1"),
        302: (1, UID, "15-00:00:00", "0:00.05", "0:00.05", "/u/Library/Caches/ms-playwright/chromium-1234/chrome --type=x"),
        303: (1, UID, "20:00:00", "0:02.00", "0:02.00", "/usr/bin/node /x/playwright-core/lib/entry/cliDaemon.js s2"),
        401: (1, UID, "03:00:00", "150:00.00", "150:04.00", "next-server (v16.3.6)"),
        404: (1, UID, "03:00:00", "10:00.00", "10:04.00", "/usr/bin/node /w/node_modules/.bin/vite --host"),
        402: (1, UID, "08:00:00", "0:10.00", "0:10.00", "next-server (v16.3.6)"),
        403: (77, UID, "08:00:00", "0:10.00", "0:10.00", "next-server (v16.3.6)"),
        501: (1, UID, "10-00:00:00", "1:00.00", "1:00.00", "/u/agent-cli/.local/bin/cursor-agent --use-system-ca idx.js"),
        502: (1, UID, "00:50:00", "0:01.00", "0:01.00", "/u/agent-cli/.local/bin/cursor-agent --use-system-ca idx.js"),
        601: (1, UID, "00:20:00", "1:00.00", "1:08.00", "/usr/bin/node /u/fnm/bin/yarn install"),
        701: (1, 0, "9-00:00:00", "0:00.00", "0:00.00", "/usr/bin/node /x/npx/root-mcp/cli.js"),
        702: (1, UID, "9-00:00:00", "0:00.00", "0:00.00",
              "/Applications/Google Drive.app/Contents/MacOS/crashpad_handler --annotation=enable_mcp_ipc_server=off"),
        703: (1, UID, "9-00:00:00", "0:00.00", "0:00.00",
              "/Applications/Foo.app/Contents/MacOS/Foo Helper --enable-blink-features=WebMCP"),
        704: (1, UID, "9-00:00:00", "0:00.00", "0:00.00", "/usr/bin/node /x/_npx/abc/node_modules/.bin/mcp-server-git"),
        705: (1, UID, "9-00:00:00", "0:00.00", "0:00.00", "/opt/homebrew/bin/1password-mcp --stdio"),
        706: (1, UID, "07:00:00", "0:01.00", "0:01.00", "/usr/bin/python3 /Users/x/Coding/mcp-evals/run_eval.py --hours 12"),
        707: (1, UID, "07:00:00", "0:01.00", "0:01.00", "/usr/bin/node /u/.npm/_npx/ef/node_modules/@playwright/mcp/cli.js --port 8931"),
        708: (1, UID, "07:00:00", "0:01.00", "0:01.00", "/usr/bin/node /k/node_modules/nx/dist/src/project-graph/plugins/isolation/plugin-worker.js"),
        801: (1, UID, "9-00:00:00", "0:01.00", "0:01.00", "/usr/bin/node /x/npx/swapped-mcp/cli.js"),
    }

    def table(index, overrides=None):
        lines = []
        for pid, (ppid, uid, etime, t1, t2, command) in rows.items():
            if overrides and pid in overrides:
                command = overrides[pid]
            lines.append(f"{pid} {ppid} {uid} {etime} {t1 if index == 0 else t2} {command}")
        return "\n".join(lines) + "\n"

    before, after = tmp / "before.txt", tmp / "after.txt"
    before.write_text(table(0))
    after.write_text(table(1, {801: "/usr/bin/node /x/unrelated-reused-pid.js"}))

    out = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--dry-run", "--json", "--sample-seconds", "5",
         "--ps-before", str(before), "--ps-after", str(after), "--now", str(NOW), "--uid", str(UID)],
        capture_output=True, text=True, check=True,
    ).stdout
    decisions = {item["pid"]: item for item in json.loads(out)}
    actions = {pid: item["action"] for pid, item in decisions.items()}

    expected = {
        101: "stop",    # nx daemon whose workspace is gone
        103: "stop",    # nx daemon idle 2h by handled-request time, despite fresh watcher lines
        109: "stop",    # nx daemon whose nested workspace is gone
        201: "stop",    # reparented MCP server, idle, 7h
        202: "stop",    # reparented tsserver, idle, 5h
        204: "stop",    # reparented biome lsp-proxy, 16d
        301: "stop",    # Playwright CLI daemon idle 15d
        302: "stop",    # Playwright browser idle 15d
        401: "stop",    # wedged reparented dev server (80% now, 83% over its lifetime)
        402: "report",  # idle reparented dev server
        501: "report",  # cursor-agent idle 10d
        601: "report",  # reparented yarn install is never killed
        704: "stop",    # reparented npx MCP server binary
        705: "stop",    # reparented *mcp binary
        708: "stop",    # reparented Nx 22 plugin worker
    }
    assert actions == expected, json.dumps({"got": actions, "want": expected}, indent=1)
    mcp_out = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--mcp-only", "--dry-run", "--json", "--sample-seconds", "5",
         "--ps-before", str(before), "--ps-after", str(after), "--now", str(NOW), "--uid", str(UID)],
        capture_output=True, text=True, check=True,
    ).stdout
    mcp_actions = {item["pid"]: item["action"] for item in json.loads(mcp_out)}
    assert mcp_actions == {201: "stop", 704: "stop", 705: "stop"}, mcp_actions

    # Untouched on purpose: 102 busy daemon, 104 young daemon, 105 daemon without a log,
    # 106 daemon with an attached listener, 107 pnpm-layout daemon resolved to its workspace,
    # 108 workspace path with a space (unrecoverable from ps), 203 MCP with a live parent,
    # 205 busy MCP, 206 tsserver under the 6h orphan threshold, 303 Playwright daemon under 24h, 403 dev server with a live parent,
    # 502 young cursor-agent, 701 another user's process,
    # 702/703 app helpers whose flags merely mention MCP, 706 user script under an mcp-named folder,
    # 707 HTTP MCP server (PPID 1 by design), 404 healthy dev server in a rebuild burst, 801 pid reused between samples.

print("PASS: default rules, MCP-only CLI, uid and pid-reuse guards")
