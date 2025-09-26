"""A script that adds a simple buffer switching utility.

Simply run this script as:

    py3file bufsel.py
"""
from __future__ import annotations

import functools

from vpe import vim, KeyHandler
from vpe.user_commands import Namespace, SimpleCommandHandler

import vpe

switcher: Switcher | None = None

handle_keys = functools.partial(KeyHandler.mapped, 'normal')


class SwitcherView(vpe.ScratchBuffer, KeyHandler):
    """The buffer used to list and select buffers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_map_keys()
        self.info.buf_map: dict[int, int] = {}

    @property
    def info(self) -> vpe.Struct:
        """The informational store associated with this buffer.

        Attributes are not allowed to be set on a ScratchBuffer because it
        is a subclasses of Vim's built-in buffer class. So we use a special
        associated store.
        """
        return self.store('info')

    def update(self, current_buf: vpe.Buffer) -> None:
        """Update the contents to match the currently available buffers."""
        lines = []
        self.info.buf_map = {}
        for i, buf in enumerate(vim.buffers):
            m = '+' if buf.options.modified else ' '
            ro = '\\[RO]' if buf.options.readonly else '    '
            name = self.escape_rich_like(buf.name)
            if buf is current_buf:
                name = f'[MoreMsg]{name}[]'
            if not buf.options.modifiable:
                ro = '[Special]\\[RO][]'
            lines.append(f'{buf.number:3}: {m}{ro} {name}')
            self.info.buf_map[i] = buf.number
        self.set_rich_like_lines(lines)

    def show(self) -> None:
        """Show this buffer, saving the current buffer."""
        if vim.current.buffer is not self:
            self.update(vim.current.buffer)
            self.info.prev_buffer = vim.current.buffer
            super().show()

    def restore(self) -> None:
        """Restore the buffer that was previously showing."""
        self.info.prev_buffer, buf = None, self.info.prev_buffer
        if buf:
            vim.current.buffer = buf

    @handle_keys('<Enter>')
    def switch_to_buffer_under_cursor(self) -> None:
        """Switch to the buffer on the cursor's line."""
        r, c = vim.current.window.cursor
        buf_num = self.info.buf_map.get(r - 1, 1)
        vim.current.buffer = vim.buffers[buf_num]

    @handle_keys(['q', '<esc>'])
    def close(self) -> None:
        """Close the buffer list without switching."""
        self.restore()


class Switcher(SimpleCommandHandler):
    """A class that provides the buffer switching control."""

    def __init__(self):
        super().__init__(command_name='Buffers')
        self.buf = vpe.get_display_buffer('switcher', buf_class=SwitcherView)

    def handle_command(self, _args: Namespace):
        """Process the Buffers command."""
        self.buf.show()


# Only create a ``Switcher`` instance the first time this is executed.
if not vim.vars.switcher_loaded:
    switcher = Switcher()
    vim.vars.switcher_loaded = 1
