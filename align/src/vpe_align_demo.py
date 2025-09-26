"""A plugin that helps align text in various ways."""
from __future__ import annotations

from vpe import vim
from vpe.user_commands import Namespace, SimpleCommandHandler

import vpe

# This is set bu the init() function, which is called by VPE.
aligner: Aligner | None = None


class Aligner(SimpleCommandHandler):
    """A class provides the Justify command."""

    # Setting the range class variable allows the Justify command to work with
    # Vim ranges/selections.
    range = True

    def __init__(self):
        super().__init__(command_name='Align')

    def add_arguments(self) -> None:
        """Add the Align command arguments."""
        self.parser.add_argument(
            'delim',
            help='The deliminator text to be aligned.')
        self.parser.add_argument(
            '--right', action='store_true',
            help='Put padding to the right of the delim.')
        self.parser.add_argument(
            '--spaces', type=int, default=-1,
            help='Set max spaces before delim, -1 means do not remove spaces.')

    def handle_command(self, args: Namespace):
        """Process the Align command."""
        # The ``cmd_info`` attribute gives us the Vim line range, which we want
        # as a Python range.
        a, b = self.cmd_info.line1 - 1, self.cmd_info.line2

        # Find the position of the delimator in each line and the length of the
        # text before the deliminator.
        buf = vim.current.buffer
        lines = buf[a:b]
        newlines = []

        # Split each line into the text before the delimieter, the delimieter
        # and the text after the deliminator.
        splits = [line.partition(args.delim) for line in buf[a:b]]
        lefts, delims, rights = list(zip(*splits))

        # Work out the furthest right position of the deliminator.
        if args.right:
            pos = max(
                (len(right) - len(right.lstrip()) + len(left) + len(delim)
                for left, delim, right in splits if delim),
                default=-1)
            if pos < 0:
                return  # No line contained the deliminator.

            lefts = [
                f'{left}{delim}'.rstrip()
                for left, delim in zip(lefts, delims)]
            rights = [right.lstrip() for right in rights]
            if args.spaces >= 0:
                pos = max(
                    len(left) for left, delim in zip(lefts, delims) if delim)
        else:
            lefts = [left.rstrip() for left in lefts]
            pos = max(
                (len(left) for left, delim in zip(lefts, delims) if delim),
                default=-1)
            if pos < 0:
                return  # No line contained the deliminator.

        if args.spaces >= 0:
            pos += args.spaces

        for left, delim, right in zip(lefts, delims, rights):
            if delim:
                if args.right:
                    newlines.append(f'{left:{pos}}{right}')
                else:
                    newlines.append(f'{left:{pos}}{delim}{right}')
            else:
                newlines.append(left)

        # Replace the selected lines.
        buf[a:b] = newlines


def init() -> None:
    """Initialise this plugin.

    This is automatically invoked by VPE.
    """
    global aligner

    # Just create the Aligner instance.
    aligner = Aligner()
