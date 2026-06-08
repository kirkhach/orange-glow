# orange-glow

A Windows ambient indicator that glows orange in the bottom-left corner of your screen
when **Claude Code / Cowork needs you** — i.e. it finishes a task or stops to ask for
input — and clears the moment you re-engage. A quiet "your move" light so you can look
away while Claude works and glance back when it's your turn. Think of it as the Windows
equivalent of a Hammerspoon script for macOS.

> This is a fork of [vasudhah-arch/orange-glow](https://github.com/vasudhah-arch/orange-glow).
> All credit for the core daemon/indicator goes to the original author. This fork flips
> the default direction to "glow when it's your move" and adds a **Cowork notification
> watcher**. The original "glow while Claude is working" behavior is still available as
> [Classic mode](#classic-mode-glow-while-claude-works).

## How it works

- A small frameless always-on-top window sits in the bottom-left corner
- It **lights up when Claude stops or needs your input**, and disappears once you reply or
  approve an action
- Driven automatically via Claude Code hooks
- Toggle on/off anytime with `Ctrl+Shift+G`

## Requirements

- Windows 10/11
- Python 3.10+
- Claude Code CLI (and/or the Claude desktop app)

## Setup

### 1. Install dependencies

```powershell
cd orange-glow
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 2. Add Claude Code hooks ("your move" mode)

Add the following to your Claude Code global settings (`~/.claude/settings.json`). This
shows the glow when Claude finishes or needs input (`Stop`, `Notification`) and hides it
when you re-engage (`UserPromptSubmit`, `PreToolUse`). Replace `C:/path/to/orange-glow`
with your actual folder path:

```json
{
  "hooks": {
    "Stop":             [ { "matcher": "", "hooks": [ { "type": "command", "command": "\"C:/path/to/orange-glow/.venv/Scripts/pythonw.exe\" \"C:/path/to/orange-glow/glow_show.py\"" } ] } ],
    "Notification":     [ { "matcher": "", "hooks": [ { "type": "command", "command": "\"C:/path/to/orange-glow/.venv/Scripts/pythonw.exe\" \"C:/path/to/orange-glow/glow_show.py\"" } ] } ],
    "UserPromptSubmit": [ { "matcher": "", "hooks": [ { "type": "command", "command": "\"C:/path/to/orange-glow/.venv/Scripts/pythonw.exe\" \"C:/path/to/orange-glow/glow_hide.py\"" } ] } ],
    "PreToolUse":       [ { "matcher": "", "hooks": [ { "type": "command", "command": "\"C:/path/to/orange-glow/.venv/Scripts/pythonw.exe\" \"C:/path/to/orange-glow/glow_hide.py\"" } ] } ]
  }
}
```

`pythonw.exe` (rather than `python.exe`) keeps the hooks windowless so no console flashes
on every tool call.

### 3. Start the daemon

Double-click `launch_glow.bat`, or run:

```powershell
& ".\.venv\Scripts\pythonw.exe" glow_daemon.py
```

### 4. (Optional) Cowork notification watcher

Autonomous (cloud) Cowork sessions run in a remote VM, so their hooks can't reach the
local glow pipe. The watcher (`glow_cowork_watcher.py`) instead reads the **Windows
notification database** (read-only) and lights the glow whenever the Claude desktop app
raises a notification ("task done / needs input"), clearing it once you dismiss the
notification. No extra dependencies beyond `pywin32`.

```powershell
# one-off checks
.venv\Scripts\python.exe glow_cowork_watcher.py --discover    # list current Claude notifications
.venv\Scripts\python.exe glow_cowork_watcher.py --self-test   # toggle the glow to test the pipe

# run it (windowless), alongside launch_glow.bat
launch_cowork_watcher.bat
```

Tunables live at the top of `glow_cowork_watcher.py` (`POLL_SECONDS`, `MAX_PERSIST_SECONDS`, `APP_MATCH`).

> Note: the watcher keys off any Claude desktop notification, so it can't perfectly
> distinguish a Cowork "your move" from other Claude toasts — but in practice those
> notifications are the your-move moments.

### 5. (Optional) Auto-start on boot

To launch the daemon (and watcher) automatically at every logon, drop shortcuts into your
Startup folder. Press `Win+R`, run `shell:startup`, and create shortcuts pointing to:

- Target: `C:\path\to\orange-glow\.venv\Scripts\pythonw.exe`  Argument: `glow_daemon.py`
- Target: `C:\path\to\orange-glow\.venv\Scripts\pythonw.exe`  Argument: `glow_cowork_watcher.py`

(Set each shortcut's "Start in" to your `orange-glow` folder.)

## Usage

| Action | How |
|---|---|
| Start the glow daemon | Double-click `launch_glow.bat` |
| Start the Cowork watcher | Double-click `launch_cowork_watcher.bat` |
| Dismiss the glow now | Click the **×** in the box's top-right corner (hides it, with a brief cooldown) |
| Disable when distracting | `Ctrl+Shift+G` (toggles on/off) |
| Re-enable | `Ctrl+Shift+G` again |
| Stop completely | Close the daemon / watcher task |

## Classic mode (glow while Claude works)

Prefer the original behavior — glow *while* Claude is processing, off when it stops? Use
these hooks instead of the ones in step 2:

```json
{
  "hooks": {
    "PreToolUse": [ { "matcher": "", "hooks": [ { "type": "command", "command": "\"C:/path/to/orange-glow/.venv/Scripts/pythonw.exe\" \"C:/path/to/orange-glow/glow_show.py\"" } ] } ],
    "Stop":       [ { "matcher": "", "hooks": [ { "type": "command", "command": "\"C:/path/to/orange-glow/.venv/Scripts/pythonw.exe\" \"C:/path/to/orange-glow/glow_hide.py\"" } ] } ]
  }
}
```

## Uninstall

1. Remove the hook entries from `~/.claude/settings.json`
2. Remove any Startup-folder shortcuts you created
3. Delete this folder

If you only delete the folder, the hooks will silently fail with no errors or slowdowns.
