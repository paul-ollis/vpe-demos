"""Using a separate log instead of using the VPE log."""

import sys
from itertools import count

import vpe

# Create a plugin-specific log and show the log file in its own buffer.
log = vpe.Log('My-plugin-log')
log.show()


def ping(_timer):
    """A timer callback to write a count to the log."""
    log(f'Ping {next(counter)}')


# Set up a time to write to the log in the background. Wait long enough and you
# will see the log window scroll as lines are added.
counter = count()
t = vpe.Timer(500, ping, repeat=-1)
