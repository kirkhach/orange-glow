import win32file
import sys

PIPE_NAME = r"\\.\pipe\orange_glow"

try:
    f = win32file.CreateFile(PIPE_NAME, win32file.GENERIC_WRITE, 0, None,
                             win32file.OPEN_EXISTING, 0, None)
    win32file.WriteFile(f, b"show")
    win32file.CloseHandle(f)
except Exception:
    pass  # daemon not running — silently ignore
