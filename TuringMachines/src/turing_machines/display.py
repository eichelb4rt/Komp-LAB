import os
from typing import TYPE_CHECKING

# this stuff is kinda weird (but it's needed)
if TYPE_CHECKING:
    from _curses import _CursesWindow
    Window = _CursesWindow
else:
    from typing import Any
    Window = Any


class ScrollableDisplay:
    def __init__(self, window: Window) -> None:
        self.window = window
        self.display_str = ""
        self.pos = 0

    def add(self, string: str):
        self.display_str += string

    def clear(self):
        self.display_str = ""

    def scroll(self, n_lines: int):
        self.pos += n_lines
        self.pos = max(self.pos, 0)
        self.pos = min(self.pos, self.display_str.count(os.linesep))
        self.update()

    def update(self):
        max_rows, _ = self.window.getmaxyx()
        lines = self.display_str.splitlines()
        display_end = min(self.pos + max_rows, len(lines))
        displayed_lines = lines[self.pos:display_end]
        window_str = "\n".join(displayed_lines)
        self.window.clear()
        self.window.addstr(window_str)
