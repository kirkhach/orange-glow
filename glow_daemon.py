import tkinter as tk
import threading
import sys
import time
import win32pipe
import win32file
import pywintypes

PIPE_NAME = r"\\.\pipe\orange_glow"
GLOW_WIDTH = 120
GLOW_HEIGHT = 80
PULSE_MIN = 0.5
PULSE_MAX = 1.0
PULSE_STEP = 0.03
PULSE_INTERVAL_MS = 40
HOTKEY = "ctrl+shift+g"
# After a manual click-dismiss, ignore "show" requests for this many seconds so a
# stuck/repeated signal doesn't immediately bring the glow back.
DISMISS_SUPPRESS_SECONDS = 4
# Size of the clickable dismiss hit-area (top-left corner of the glow), in pixels.
DISMISS_HIT = 26

# Gradient stops: (position 0..1, hex color)
GRADIENT = [
    (0.0,  "#FF6A00"),
    (0.25, "#FF8C00"),
    (0.55, "#FFA500"),
    (0.80, "#7A3300"),
    (1.0,  "#000000"),
]


def lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"


def build_gradient_colors(width):
    colors = []
    for x in range(width):
        t = x / (width - 1)
        # find surrounding stops
        for i in range(len(GRADIENT)-1):
            t0, c0 = GRADIENT[i]
            t1, c1 = GRADIENT[i+1]
            if t0 <= t <= t1:
                local_t = (t - t0) / (t1 - t0) if t1 > t0 else 0
                colors.append(lerp_color(c0, c1, local_t))
                break
    return colors


class GlowDaemon:
    def __init__(self):
        self.root = tk.Tk()
        self.enabled = True
        self.visible = False
        self.pulse_dir = 1
        self.pulse_alpha = PULSE_MAX
        self.suppress_until = 0.0
        self._setup_window()
        self._setup_hotkey()
        self._start_pipe_listener()

    def _setup_window(self):
        root = self.root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", "black")
        root.attributes("-alpha", 1.0)
        root.configure(bg="black")

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x_pos = 0
        y_pos = sh - GLOW_HEIGHT
        root.geometry(f"{GLOW_WIDTH}x{GLOW_HEIGHT}+{x_pos}+{y_pos}")

        self.canvas = tk.Canvas(root, width=GLOW_WIDTH, height=GLOW_HEIGHT,
                                bg="black", highlightthickness=0)
        self.canvas.pack()

        # horizontal gradient (left=bright, right=transparent)
        h_colors = build_gradient_colors(GLOW_WIDTH)
        for x, color in enumerate(h_colors):
            self.canvas.create_line(x, 0, x, GLOW_HEIGHT, fill=color)

        # Small dismiss button in the top-right corner. The glow fades to the
        # window's transparent color on the right, so we draw a solid amber chip
        # as a backing — that makes the x both visible and reliably clickable.
        r = 11
        cx, cy = GLOW_WIDTH - 12, 12
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill="#E8780A", outline="")
        self.canvas.create_text(cx, cy, text="×", fill="#0a0a0a",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.bind("<Button-1>", self._on_click)

        root.withdraw()

    def _setup_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY, self._toggle_enabled)
        except Exception as e:
            print(f"Hotkey registration failed: {e}", flush=True)

    def _toggle_enabled(self):
        self.enabled = not self.enabled
        state = "ENABLED" if self.enabled else "DISABLED"
        print(f"[orange-glow] {state} (Ctrl+Shift+G)", flush=True)
        if not self.enabled:
            self.root.after(0, self._hide)

    def _show(self):
        if not self.enabled or self.visible:
            return
        if time.time() < self.suppress_until:
            return
        self.visible = True
        self.pulse_alpha = PULSE_MAX
        self.root.deiconify()
        self._pulse()

    def _on_click(self, event):
        # The top-right corner acts as a dismiss button.
        if event.x >= GLOW_WIDTH - DISMISS_HIT and event.y <= DISMISS_HIT:
            self._dismiss()

    def _dismiss(self):
        self.suppress_until = time.time() + DISMISS_SUPPRESS_SECONDS
        self._hide()
        print("[orange-glow] dismissed via x (suppressed "
              f"{DISMISS_SUPPRESS_SECONDS}s)", flush=True)

    def _hide(self):
        if not self.visible:
            return
        self.visible = False
        self.root.withdraw()

    def _pulse(self):
        if not self.visible:
            return
        self.pulse_alpha += PULSE_STEP * self.pulse_dir
        if self.pulse_alpha >= PULSE_MAX:
            self.pulse_alpha = PULSE_MAX
            self.pulse_dir = -1
        elif self.pulse_alpha <= PULSE_MIN:
            self.pulse_alpha = PULSE_MIN
            self.pulse_dir = 1
        self.root.attributes("-alpha", self.pulse_alpha)
        self.root.after(PULSE_INTERVAL_MS, self._pulse)

    def _start_pipe_listener(self):
        t = threading.Thread(target=self._pipe_loop, daemon=True)
        t.start()

    def _pipe_loop(self):
        while True:
            try:
                pipe = win32pipe.CreateNamedPipe(
                    PIPE_NAME,
                    win32pipe.PIPE_ACCESS_INBOUND,
                    win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                    win32pipe.PIPE_UNLIMITED_INSTANCES,
                    512, 512, 0, None
                )
                win32pipe.ConnectNamedPipe(pipe, None)
                _, data = win32file.ReadFile(pipe, 512)
                win32file.CloseHandle(pipe)
                msg = data.decode().strip()
                if msg == "show":
                    self.root.after(0, self._show)
                elif msg == "hide":
                    self.root.after(0, self._hide)
            except pywintypes.error:
                pass
            except Exception as e:
                print(f"[pipe error] {e}", flush=True)

    def run(self):
        print(f"[orange-glow] daemon started. Hotkey: {HOTKEY}", flush=True)
        self.root.mainloop()


if __name__ == "__main__":
    GlowDaemon().run()
