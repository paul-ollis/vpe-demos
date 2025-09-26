"""Ways to write to the VPE for debugging log."""

import sys
from itertools import count

import vpe

# Show the log file in its own buffer.
vpe.log.show()

# A clean log is easier to read.
vpe.log.clear()

# For debugging, you should use the ``log`` instance directly rather than using
# print().
#
# The ``log`` object is callable, acting much like ``print``.
vpe.log('Running inside Vim with Python', sys.version)

# The log.write() method just takes a string.
vpe.log.write('Still running inside Vim with Python {sys.version_info}')


def ping(_timer):
    """A timer callback to write a count to the log."""
    vpe.log(f'Ping {next(counter)}')


# Set up a time to write to the log in the background. Wait long enough and you
# will see the log window scroll as lines are added.
counter = count()
t = vpe.Timer(500, ping, repeat=-1)
