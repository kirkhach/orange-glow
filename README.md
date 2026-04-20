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
