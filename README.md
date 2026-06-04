# orange-glow

A Windows ambient indicator that glows orange on the bottom-left corner of your screen while Claude Code is processing. Think of it as the Windows equivalent of a Hammerspoon script for macOS.

## How it works

- A small frameless always-on-top window sits in the bottom-left corner
- It pulses orange while Claude is thinking, disappears when Claude stops
- Triggered automatically via Claude Code hooks
- Toggle on/off anytime with `Ctrl+Shift+G`

## Requirements

- Windows 10/11
- Python 3.10+
- Claude Code CLI

## Setup

### 1. Install dependencies

```powershell
cd orange-glow
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 2. Add Claude Code hooks

Add the following to your Claude Code global settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:/path/to/orange-glow/.venv/Scripts/python.exe\" \"C:/path/to/orange-glow/glow_show.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:/path/to/orange-glow/.venv/Scripts/python.exe\" \"C:/path/to/orange-glow/glow_hide.py\""
          }
        ]
      }
    ]
  }
}
```

Replace `C:/path/to/orange-glow` with your actual folder path.

### 3. Start the daemon

Double-click `launch_glow.bat`, or run:

```powershell
& ".\venv\Scripts\pythonw.exe" glow_daemon.py
```

## Usage

| Action | How |
|---|---|
| Start the glow daemon | Double-click `launch_glow.bat` |
| Disable when distracting | `Ctrl+Shift+G` (toggles on/off) |
| Re-enable | `Ctrl+Shift+G` again |
| Stop completely | Close the daemon terminal / task |

## Uninstall

1. Remove the hook entries from `~/.claude/settings.json`
2. Delete this folder

If you only delete the folder, the hooks will silently fail with no errors or slowdowns.

---

## Fork additions

This fork adds two things on top of the upstream project. All credit for the core
daemon/indicator goes to the original author ([vasudhah-arch/orange-glow](https://github.com/vasudhah-arch/orange-glow)).

### 1. Inverted mode — glow = "your move"

Instead of glowing *while* Claude works, you can flip it so the glow means **Claude is
done or waiting on you**, and it clears the moment you re-engage. Use these hooks in
`~/.claude/settings.json` (replace `C:/path/to/orange-glow` with your folder, and prefer
`pythonw.exe` over `python.exe` to avoid console flashes):

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

### 2. Cowork notification watcher (`glow_cowork_watcher.py`)

Autonomous (cloud) Cowork sessions run in a remote VM, so their hooks can't reach the
local glow pipe. This watcher instead reads the **Windows notification database**
(read-only) and lights the glow whenever the Claude desktop app raises a notification
("task done / needs input"), clearing it once you dismiss the notification. No extra
dependencies beyond `pywin32`.

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
