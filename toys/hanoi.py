"""A script that runs a Tower of Hanoi animation.

Simply run this script as:

    py3file hanoi.py
"""
from __future__ import annotations

import time
from collections.abc import Iterator

from vpe import vim
from vpe.user_commands import Namespace, SimpleCommandHandler

import vpe

# This gets set to a `Hanoi` instance the first time this is run.
hanoi: Hanoi | None = None


class Hanoi(SimpleCommandHandler):
    """A class that run the Hanoi animation within a Vim buffer.

    Each tower is represented by a list, where each entry is the size of a disc
    within the tower. A complete tower of 5 discs is represented
    as [5, 4, 3, 2, 1], em empty tower is simply [] and [5, 3] is a tower with
    a disc of size 3 on top of a disc of size 5.
    """

    mover: Iterator[None]
    towers: tuple[list[int], list[int], list[int]]
    timer = vpe.Timer

    def __init__(self):
        # Get the buffer that we want to display the tower in.
        super().__init__(command_name='Hanoi')
        self.buf = vpe.get_display_buffer('hanoi')
        self.resume_time = 0.0
        self.n_discs = 5
        self.delay_ms = 500
        self.start()

    def add_arguments(self) -> None:
        """Add the Hanoi command arguments."""
        self.parser.add_argument(
            '--height', type=int, default=5,
            help='The height of the start tower (2 to 20), default=5')
        self.parser.add_argument(
            '--delay', type=float, default=0.5,
            help='The delay between moves in seconds (0.1 to 60.0)'
                 ', default=0.5')
        self.parser.add_argument(
            '--show', action='store_true',
            help='Try to make sure the Hanoi buffer is visible')

    def handle_command(self, args: Namespace):
        """Process the Hanoi command."""
        if args.show:
            self.show()
            return

        self.n_discs = max(2, min(20, args.height))
        self.delay_ms = int( 1000 * max(0.1, min(60.0, args.delay)))
        self.start()

    def start(self) -> None:
        """Start the animation."""
        self.timer = vpe.Timer(self.delay_ms, self.update, repeat=-1)
        self.towers = (list(range(self.n_discs, 0, -1)), [], [])
        self.mover = self.generate_moves(self.n_discs, *self.towers)
        self.show()
        self.draw()

    def show(self) -> None:
        """Make sure the buffer is showing in a window.

        If not visible then the current window is split.
        """
        if self.buf.find_best_active_window() is None:
            self.buf.show(splitlines=-self.n_discs)

        # Try to ensure that the window is tall enough to show the whole tower.
        win = self.buf.find_best_active_window()
        if vim.winheight(win.number) < self.n_discs:
            with vpe.temp_active_window(win):
                vpe.commands.resize(self.n_discs)

    def update(self, _timer) -> None:
        """Make a single move and update the buffer."""
        if self.resume_time > 0.0:
            if time.time() >=self.resume_time:
                self.resume_time = 0.0
                self.start()
            return

        try:
            next(self.mover)
        except StopIteration:
            self.resume_time = time.time() + 3.0
        self.draw()

    def draw(self):
        """Draw the current tower configuration."""
        lines = []
        width = self.n_discs * 2 + 1
        for row in range(self.n_discs):
            line = []
            for tower in self.towers:
                try:
                    size = tower[row]
                except IndexError:
                    size = 0
                disc = '=' * (size * 2 + 1) if size else ':'
                line.append(disc.center(width))
            lines.append('  '.join(line))

        with self.buf.modifiable():
            self.buf[:] = list(reversed(lines))

    def generate_moves(self, n, pa, pb, pc) -> Iterator[None]:
        """Make single move."""
        if n == 0:
            return
        yield from self.generate_moves(n - 1, pa, pc, pb)
        if pa:
            pc.append(pa.pop())
            yield
        yield from self.generate_moves(n - 1, pb, pa, pc)


# Only create a ``Hanoi`` instance the first time this is executed.
if not vim.vars.hanoi_loaded:
    hanoi = Hanoi()
    vim.vars.hanoi_loaded = 1
