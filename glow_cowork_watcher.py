"""
glow_cowork_watcher.py
----------------------
Drives the orange-glow daemon based on Windows toast notifications raised by the
Claude desktop app. Intended for autonomous (cloud) Cowork sessions, whose hooks
run in a remote VM and therefore cannot reach the local glow pipe. Instead we
watch the local Windows notification database: when the desktop app raises a
"your move" notification (task done / needs input), we light the glow; when you
clear it from Action Center (i.e. you've acted on it), we hide the glow.

No third-party deps beyond pywin32 (already installed). Reads the notification DB
strictly read-only.

Usage:
    pythonw glow_cowork_watcher.py            # run silently (normal use)
    python  glow_cowork_watcher.py --verbose  # run with console logging
    python  glow_cowork_watcher.py --discover # list current Claude notifications and exit
    python  glow_cowork_watcher.py --self-test# show glow for 3s then hide, to prove the pipe works
"""

import os
import sys
import time
import sqlite3
import argparse

# ---- Config (tweak to taste) ------------------------------------------------
DB_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db"
)
# Match the Claude desktop app's notification handler id (case-insensitive substring).
APP_MATCH = "claude_pzs8sxrjxfjjc"
PIPE_NAME = r"\\.\pipe\orange_glow"
POLL_SECONDS = 2.0
# A notification we never clear stops glowing after this many seconds (safety net).
MAX_PERSIST_SECONDS = 30 * 60
# FILETIME epoch (1601-01-01) -> Unix epoch (1970-01-01), in seconds.
FILETIME_UNIX_DELTA = 11644473600
# -----------------------------------------------------------------------------


def now_filetime():
    """Current time as Windows FILETIME (100-ns ticks since 1601-01-01 UTC)."""
    return int((time.time() + FILETIME_UNIX_DELTA) * 10_000_000)


def filetime_age_seconds(ft):
    return (now_filetime() - ft) / 10_000_000.0


def send_pipe(msg, verbose=False):
    """Write 'show'/'hide' to the glow daemon. Silently ignore if daemon is down."""
    try:
        import win32file
        f = win32file.CreateFile(
            PIPE_NAME, win32file.GENERIC_WRITE, 0, None,
            win32file.OPEN_EXISTING, 0, None,
        )
        win32file.WriteFile(f, msg.encode())
        win32file.CloseHandle(f)
        if verbose:
            print(f"[pipe] sent {msg!r}", flush=True)
    except Exception as e:
        if verbose:
            print(f"[pipe] daemon not reachable ({e}) - ignoring", flush=True)


def query_claude_notifications():
    """Return list of (Id, ArrivalTime) for current Claude notifications.

    Opens the DB read-only each call so we always see the latest committed rows.
    Returns None if the DB can't be read this tick (transient lock, etc.)."""
    uri = f"file:{DB_PATH}?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True, timeout=1.5)
    except Exception:
        return None
    try:
        con.row_factory = sqlite3.Row
        q = """
            SELECT n.Id AS id, n.ArrivalTime AS arrival
            FROM Notification n
            JOIN NotificationHandler h ON n.HandlerId = h.RecordId
            WHERE lower(h.PrimaryId) LIKE ?
        """
        rows = con.execute(q, (f"%{APP_MATCH}%",)).fetchall()
        return [(int(r["id"]), int(r["arrival"])) for r in rows]
    except Exception:
        return None
    finally:
        con.close()


def discover():
    rows = query_claude_notifications()
    if rows is None:
        print("Could not read the notification DB.")
        return
    if not rows:
        print(f"No notifications currently match {APP_MATCH!r}.")
        print("Tip: trigger a Claude/Cowork notification, then re-run --discover.")
        return
    rows.sort(key=lambda r: r[0], reverse=True)
    print(f"{len(rows)} Claude notification(s) currently in Action Center:")
    for nid, arrival in rows[:25]:
        age = filetime_age_seconds(arrival)
        print(f"  id={nid}  age={age:7.1f}s")


def self_test():
    print("Sending 'show' (glow should appear bottom-left)...")
    send_pipe("show", verbose=True)
    time.sleep(3)
    print("Sending 'hide' (glow should disappear)...")
    send_pipe("hide", verbose=True)
    print("Done. If you saw the glow toggle, the pipe link works.")


def run(verbose=False):
    rows = query_claude_notifications()
    if rows is None:
        rows = []
    baseline_max_id = max((r[0] for r in rows), default=0)
    start_ft = now_filetime()
    seen = set(r[0] for r in rows)   # ignore the pre-existing backlog
    active = {}                      # id -> arrival_ft (notifications we're glowing for)
    glow_on = False

    if verbose:
        print(f"[watcher] started. baseline_max_id={baseline_max_id}, "
              f"ignoring {len(seen)} pre-existing notification(s).", flush=True)

    while True:
        rows = query_claude_notifications()
        if rows is not None:
            cur_ids = set(r[0] for r in rows)
            arrivals = dict(rows)

            # New notifications that arrived after we started.
            for nid, arrival in rows:
                if nid not in seen:
                    seen.add(nid)
                    if nid > baseline_max_id and arrival >= start_ft:
                        active[nid] = arrival
                        if verbose:
                            print(f"[watcher] new notification id={nid}", flush=True)

            # Drop notifications that were cleared from Action Center (you acted on it).
            for nid in list(active):
                if nid not in cur_ids:
                    del active[nid]
                    if verbose:
                        print(f"[watcher] notification id={nid} cleared", flush=True)

            # Safety: age out notifications you never cleared.
            for nid in list(active):
                if filetime_age_seconds(active[nid]) > MAX_PERSIST_SECONDS:
                    del active[nid]
                    if verbose:
                        print(f"[watcher] notification id={nid} aged out", flush=True)

            desired_on = len(active) > 0
            if desired_on and not glow_on:
                send_pipe("show", verbose=verbose)
                glow_on = True
            elif not desired_on and glow_on:
                send_pipe("hide", verbose=verbose)
                glow_on = False

        time.sleep(POLL_SECONDS)


def main():
    ap = argparse.ArgumentParser(description="Drive orange-glow from Claude desktop notifications.")
    ap.add_argument("--verbose", action="store_true", help="log to console")
    ap.add_argument("--discover", action="store_true", help="list current Claude notifications and exit")
    ap.add_argument("--self-test", action="store_true", help="toggle the glow once to test the pipe")
    args = ap.parse_args()

    if args.discover:
        discover()
    elif args.self_test:
        self_test()
    else:
        run(verbose=args.verbose)


if __name__ == "__main__":
    main()
