"""A Sokoban game.

This is pretty much a clone of:

    https://www.vim.org/scripts/script.php?script_id=211

It uses the same set of levels which originated from
http://www.cs.cornell.edu/andru/xsokoban.html

Simply run this script as::

       py3file sokoban.py
"""
from __future__ import annotations

import inspect
import json
import zipfile
from pathlib import Path
from typing import Iterable, TypeAlias

import vpe
from vpe import vim
from vpe.mapping import KeyHandler, MappingInfo
from vpe.user_commands import Namespace, SimpleCommandHandler

PropertySpec: TypeAlias = [int, int, str]

MIN_HEIGHT = 40         # Height to allow for the game display.
GRID_OFFSET = 10        # The game grid is indented b this number of spaces.
WIDTH = 78              # The nominal width to assume for the game window.
MAX_MOVES = 1_000_000   # Used to indicate no best score yet.

# Mapping from character to highlight group.
char_to_highlight = {
    'X': 'Error',
    '#': 'Number',
    '$': 'Comment',
    '.': 'Keyword',
}

# Mapping from motion key to the x, y increment values.
motion_to_inc = {
    'h': (-1, 0),   '<Left>': (-1, 0),
    'j': (0, 1),    '<Down>': (0, 1),
    'k': (0, -1),   '<Up>': (0, -1),
    'l': (1, 0),    '<Right>': (1, 0),
}

# This gets set to a `Sokoban` instance the first time this is run.
sokoban: Sokoban | None = None

header = [
    '                           SOKOBAN DEMO',
    '                           ============',
    'Score                                        Key',
    '-----                                        ---',
    'Level:  xx                                  X = soko    # = wall',
    'Moves:  xxxx                                $ = package . = home',
    'Pushes: xxxx',
    '',
    '........................................................................',
    '    k      Move "soko"          u Undo          n next',
    '  h   l    Of use the           r Restart       p previous',
    '    j      arrow keys',
    '------------------------------------------------------------------------',
    '',
    '',
]
# The ``markup_text`` method adds special Python-Rich-like markup. For example
# the first line below wraps the 'X' as '[Error]X[]'. The Buffer's
# set_rich_like_lines method interprets this markup, adding Vim text properties
# to the buffer to show the 'X' using the 'Error' highlight group.
header[4] = vpe.Buffer.markup_text(header[4], 'X', 'Error')
header[4] = vpe.Buffer.markup_text(header[4], '#', 'Number')
header[5] = vpe.Buffer.markup_text(header[5], '$', 'Comment')
header[5] = vpe.Buffer.markup_text(header[5], '.', 'Keyword')

complete_text = """
  .---------------------------------------------------.
  |                   LEVEL COMPLETE                  |
  |        moves: : mmmm          pushes: pppp        |
  | (r)estart level, (p)revious level or (n)ext level |
  `---------------------------------------------------'"""


def _find_zip_file() -> Path:
    """Find where the zipfile containing the levels is.

    If this were a proper VPE plugin, then this file would have been imported
    and we would use ``__file__``, but since this is a toy demo which we
    expect to have been started as::

        ``py3file sokoban.py`` or ``py3file toys/sokoban.py``

    So we look in the current directory and also try a 'toys' subdirectory.
    """
    zip_path = Path('levels.zip')
    if not zip_path.exists():
        zip_path = Path('toys/levels.zip')
        if not zip_path.exists():
            msg = 'Could not find file levels.zip'
            msg += '\nTry starting this in the toys directory.'
            raise RunttimeError(msg)
    return zip_path


def _find_saved_file() -> Path:
    """Find where to save/load the high scores and current level.

    We use the same directory as the levels zip file.
    """
    return _find_zip_file().parent / 'saved.json'


class LevelStore:
    """Source of the levels."""
    def __init__(self):
        self.zip = zipfile.ZipFile(_find_zip_file())

    def retrieve_content(self, level: int) -> list[str]:
        """The text for this level."""
        text = self.zip.read(f'level{level}.sok')
        return [
            line.replace('@', 'X')
            for line in text.decode('utf-8').splitlines()]

    def __len__(self) -> int:
        return len(self.zip.namelist())


class View(vpe.ScratchBuffer, vpe.KeyHandler):
    """The buffer used to render the Sokoban game display."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_map_keys(pass_info=True)
        self.info.control = None
        with self.modifiable():
            self.set_rich_like_lines(header)
        self.info.level_line = self[4]
        self.info.moves_line = self[5]
        self.info.pushes_line = self[6]
        self.info.header_len = len(header)

    @property
    def info(self) -> vpe.Struct:
        """The information store for this buffer."""
        return self.store('info')

    @KeyHandler.mapped(mode='normal', keyseq=[
            'h', 'j', 'k', 'l', '<Left>', '<Down>', '<Up>', '<Right>'])
    def handle_motion_key(self, info: MappingInfo) -> None:
        """Forward a motion key to the controller."""
        self.info.control.handle_motion_key(info)

    @KeyHandler.mapped(mode='normal', keyseq=['u', 'r', 'n', 'p'])
    def handle_key(self, info: MappingInfo) -> None:
        """Forward non-motion key to the controller."""
        self.info.control.handle_key(info)

    def render_layout(self, puzzle: Puzzzle, state: SavedState) -> None:
        """Mark up and 'draw' the .lyout of the puzzle."""
        with self.modifiable():
            self.set_rich_like_lines(header)
        self.update_stats(1, 0, 0)
        self.update_high_score(state, 'moves')
        with self.modifiable():
            for text, props in puzzle.render_all_rows():
                self.append(text)
                self.set_line_props(len(self) - 1, props)

    def update_layout(
            self, puzzle: Puzzle, changed_lines: list[tuple[int, str]]) -> None:
        """Update changed lines and make sure stats are up to date."""
        with self.modifiable():
            for y in changed_lines:
                text, props = puzzle.render_row(y)
                lidx = y + self.info.header_len
                self[lidx] = text
                self.set_line_props(lidx, props)
        self.update_stats(puzzle.level, puzzle.move_count, puzzle.push_count)

    def render_end_of_level(self, puzzle: Puzzle) -> None:
        """Splash the end of game box on top of the game display."""
        text = complete_text.replace('mmmm', f'{puzzle.move_count:<4}')
        text = text.replace('pppp', f'{puzzle.push_count:<4}')
        lines = inspect.cleandoc(text).splitlines()
        offset = (puzzle.height - len(lines)) // 2
        start = self.info.header_len + offset
        w = len(lines[0])
        c_start = (WIDTH - w) // 2
        c_end = c_start + w
        with self.modifiable():
            for i, line in enumerate(lines):
                text, props = puzzle.render_row(i + offset)
                props = [
                    (a, b, t) for a, b, t in props
                    if not c_start <= a <= c_end]
                a = text[:c_start]
                b = text[c_start + w:]
                self[i + start] = a + line + b
                self.set_line_props(i + start, props)

    def update_stats(self, level: int, moves: int, pushes: int) -> None:
        """Update the stats in the header."""
        with self.modifiable():
            self[4] = self.info.level_line.replace('xx', f'{level:<2}')
            self[5] = self.info.moves_line.replace('xxxx', f'{moves:<4}')
            self[6] = self.info.pushes_line.replace('xxxx', f'{pushes:<4}')

    def update_high_score(self, state: SavedState, mode: str) -> None:
        """Update the high score information in the header."""
        moves, pushes = state.retrieve_best_score(mode)
        if moves is None:
            text = ''
        else:
            text = f'Best score by {mode}:  Moves={moves}  Pushes={pushes}'
        with self.modifiable():
            self[self.info.header_len-2] = text

    # This might become a method in the VPE library.
    def set_line_props(
            self,
            lidx: int,
            props: list[PropertySpec],
        ) -> None:
        """Set a set of properties for a given line.

        All previous properties on the line are cleared.
        """
        vim.prop_clear(lidx + 1, lidx + 1, {'bufnr': self.number})
        for start_cidx, end_cidx, hl_group in props:
            self.set_line_prop(lidx, start_cidx, end_cidx, hl_group)


class Puzzle:
    """Class to manage a puzzle's state."""
    def __init__(self, level_store: LevelStore, state: SavedState):
        self.grid = [
            list(line) for line in level_store.retrieve_content(state.level)]
        self.state = state
        self.height = len(self.grid)
        self.home_positions: set[tuple[int, int]] = set()
        self.move_count = 0
        self.push_count = 0
        self.undo_buffer = []
        for y, row in enumerate(self.grid):
            if 'X' in row:
                self.pos = row.index('X'), y
            for x, c in enumerate(row):
                if c == 'X':
                    self.pos = x, y
                elif c == '.':
                    self.home_positions.add((x, y))

    @property
    def level(self) -> int:
        """The current level."""
        return self.state.level

    def handle_motion(self, key: str) -> list[int]:
        """Handle an attempted movement."""
        changed_lines = []
        if self.finished:
            return changed_lines

        # Figure out the new 'soko' position and the place where any pushed
        # package will end up.
        xinc, yinc = motion_to_inc[key]
        x, y = self.pos
        x2, y2 = x + xinc, y + yinc
        x3, y3 = x + xinc * 2, y + yinc * 2

        # Bail if the move is not permitted.
        dest_char = self._char_at(x2, y2)
        match dest_char:
            case '#':
                return changed_lines  # Move not allowed
            case '$':
                if self._char_at(x3, y3) not in ' .':
                    return changed_lines  # Move not allowed

        # The move is legal. Create an undo record.
        undo = self.move_count, self.push_count, self.pos, []
        self.undo_buffer.append(undo)

        # Add to the list of changed lines, replace the
        # 'soko' with the the appropriate empty cell character.
        undo[3].append((y, ''.join(self.grid[y])))
        changed_lines.append(y)
        line = self.grid[y]
        line[x] = self._empty_char(self.pos)

        # Move any pushed package and the 'soko'.
        vertical_move = y != y2
        if vertical_move:
            undo[3].append((y2, ''.join(self.grid[y2])))
            line = self.grid[y2]
            line[x] = 'X'
            changed_lines.append(y2)
            if dest_char == '$':
                undo[3].append((y3, ''.join(self.grid[y3])))
                line = self.grid[y3]
                line[x] = '$'
                changed_lines.append(y3)
        else:
            line[x2] = 'X'
            if dest_char == '$':
                line[x3] = '$'
            changed_lines.append(y)

        # Update move counts and posision.
        self.move_count += 1
        if dest_char == '$':
            self.push_count += 1
        self.pos = x2, y2

        return changed_lines

    def undo(self) -> None:
        """Undo the last move."""
        changed_lines = []
        undo_buffer = self.undo_buffer
        if not undo_buffer or self.finished:
            return changed_lines

        self.move_count, self.push_count, self.pos, lines = undo_buffer.pop()
        for y, text in lines:
            self.grid[y] = list(text)
            changed_lines.append(y)
        return changed_lines

    @property
    def finished(self) -> bool:
        """True if the level is finished."""
        for pos in self.home_positions:
            if self._char_at(*pos) != '$':
                return False
        return True

    def _empty_char(self, pos: tuple[int, int]) -> str:
        """Get the character to show for an empty cell."""
        return '.' if pos in self.home_positions else ' '

    def _char_at(self, x: int, y: int) -> str:
        """Get the character at given position."""
        try:
            return self.grid[y][x]
        except IndexError:
            return ''

    def render_row(self, index: int) -> tuple[str, list[PropertySpec]]:
        """Render a row as text and property details."""
        line = ' ' * GRID_OFFSET + ''.join(self.grid[index])
        props = []
        for i, c in enumerate(line):
            highlight = char_to_highlight.get(c, None)
            if highlight is not None:
                props.append((i, i + 1, highlight))
        return line, props

    def render_all_rows(self) -> Iterable[tuple[str, list[PropertySpec]]]:
        """Render all the rows for this puzzle."""
        for i in range(len(self.grid)):
            yield self.render_row(i)


class SavedState:
    """Class to hold the high score table and other state.

    Two scores are stored for each level - the one with the smallest move count
    and the on with the smallest push count.
    """
    def __init__(self, n_levels: int):
        self.n_levels = n_levels
        self.saved_path = _find_saved_file()
        if self.saved_path.exists():
            self.data = json.loads(
                self.saved_path.read_text(encoding='utf-8'))
        else:
            scores = {
                str(level): [(MAX_MOVES, MAX_MOVES), (MAX_MOVES, MAX_MOVES)]
                for level in range(1, n_levels + 1)}
            self.data = {
                'level': 0,
                'scores': scores,
            }
            self.save()

    @property
    def scores(self) -> dict:
        """The scores parte of the state."""
        return self.data['scores']

    @property
    def level(self) -> int:
        """The saved level."""
        return self.data['level']

    @level.setter
    def level(self, level: int) -> int:
        """The saved level."""
        if self.data['level'] != level:
            self.data['level'] = level
            self.save()

    def select_next_level(self, step: int = 1) -> None:
        """Move on to the next level."""
        self.level += step
        self.level = max(1, min(self.level, self.n_levels))

    def retrieve_best_score(self, mode: str) -> tuple[int, int]:
        """Retrieve the best score for a level."""
        best_by_moves, best_by_pushes = self.scores[str(self.level)]
        if mode == 'moves':
            best = best_by_moves
        else:
            best = best_by_pushes
        if MAX_MOVES in best:
            return (None, None)
        else:
            return best

    def store_score(self, moves: int, pushes: int) -> None:
        """Store a new score into the table."""
        best_by_moves, best_by_pushes = self.scores[str(self.level)]

        new_entry = False
        if None in best_by_moves:
            best_by_moves = best_by_pushes = moves, pushes
            new_entry = True
        if moves < best_by_moves[0]:
            best_by_moves = moves, pushes
            new_entry = True
        if pushes < best_by_pushes[1]:
            best_by_pushes = moves, pushes
            new_entry = True

        if new_entry:
            self.scores[str(self.level)] = best_by_moves, best_by_pushes

    def save(self) -> None:
        """Save the current state."""
        self.saved_path.write_text(
            json.dumps(self.data, indent=4), encoding='utf-8')


class Sokoban(SimpleCommandHandler):
    """A class that manages the Sokoban game."""
    def __init__(self):
        # Get the buffer that we want to display the tower in.
        super().__init__(command_name='Sokoban')
        self.buf = vpe.get_display_buffer('sokoban', View)
        self.buf.info.control = self
        self.level_store = LevelStore()
        self.state = SavedState(len(self.level_store))

    def add_arguments(self) -> None:
        """Add the Align command arguments."""
        self.parser.add_argument(
            'level', nargs='?', type=int,
            help='The level to start with.')

    def handle_command(self, args: Namespace):
        """Process the Sokoban command."""
        self.start(args.level)

    def start(self, level=None, level_step: int = 1) -> None:
        """Start a new game."""
        if level is not None:
            self.state.level = level
        else:
            self.state.select_next_level(level_step)
        self.puzzle = Puzzle(self.level_store, self.state)
        self.buf.render_layout(self.puzzle, self.state)
        self.buf.update_layout(self.puzzle, [])
        self.show()

    def handle_motion_key(self, info: MappingInfo) -> None:
        """Process a key mapping."""
        new_lines = self.puzzle.handle_motion(info.keys)
        if new_lines:
            self.buf.update_layout(self.puzzle, new_lines)
            if self.puzzle.finished:
                self.state.store_score(
                    self.puzzle.move_count, self.puzzle.push_count)
                self.buf.render_end_of_level(self.puzzle)
                self.buf.update_high_score(self.state, 'moves')

    def handle_key(self, info: MappingInfo) -> None:
        """Process a key mapping."""
        match info.keys:
            case 'n':
                self.start(level_step=1)
            case 'p':
                self.start(level_step=-1)
            case 'r':
                self.start(level_step=0)
            case 'u':
                if self.puzzle:
                    new_lines = self.puzzle.undo()
                    self.buf.update_layout(self.puzzle, new_lines)
        self.buf.update_layout(self.puzzle, [])

    def show(self) -> None:
        """Make sure the buffer is showing."""
        if self.buf.find_best_active_window() is None:
            self.buf.show()

        # Try to ensure that the window is tall enough to show the game.
        win = self.buf.find_best_active_window()
        if vim.winheight(win.number) < MIN_HEIGHT:
            with vpe.temp_active_window(win):
                vpe.commands.resize(MIN_HEIGHT)


# Only create a ``Sokoban`` instance the first time this is executed.
if not vim.vars.sokoban_loaded:
    print('Create controller')
    sokoban = Sokoban()
    vim.vars.sokoban_loaded = 1
