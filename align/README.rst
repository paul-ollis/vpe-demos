A demo text alignment tool
==========================

Installation
------------

This is structured as a Vim Python Extensions (VPE) plugin, so you need to
install is as a Python library. If you are not familiar with doing this then
one approach is:

.. code-block: vim

    " Show the log file window and redirect Python print() call to the log.
    Vpe log show
    Vpe log redirect on

    " Determine which Python installation your Vim is using. This will log
    " something like ''/usr/bin/python3''.
    py3 import sys
    py3 print(sys.executable)

In a terminal run the command (we are assuming '/usr/bin/python3' was
identified from the above steps). Make sure you are in this README's directory
for the next step.:

.. code-block: sh

    /usr/bin/python3 -m pip install --user -e --break .

This will install vpe_align_demo as a Python library in a way that VPE can
discover and automatically load. The library will be installed just for your
user as an editable installation. This means you can edit src/vpe_align_demo.py
and you changes will be picked up the next time you start a Vim session.

The '--break' option is required on some Linux distributions. It is not
normally recommended to use this, but for this simple library as a user install
it is perfectly safe.

You can undo the installation as:

.. code-block: sh

    /usr/bin/python3 -m pip uninstall --break vpe_align_demo


Usage
-----

This plugin creates a command called 'Align', which has the following usage.

.. code-block: vim

    Align [--right] [--spaces={N}] {delim}

Normally you would give at range on lines for select some lines before you
execute.

This will process the selected range of lines looking for {delim} in each line.
Then the lines are reformatted so that the {delim} starts in the same column for
each line. For example, given a file containing:

.. code-block: python

    RED = 1
    ORANGE = 3
    GREEN = 2

The command ``1,3 Align --spaces=1 =``, will reformat lines 1 to 3 as:

.. code-block: python

    RED    = 1
    ORANGE = 3
    GREEN  = 2

Alternatively command ``1,3 Align --spaces=1 = --right``, will reformat lines 1 to 3 as:

.. code-block: python

    RED =    1
    ORANGE = 3
    GREEN =  2

As is common with Vim user commands, you can abbreviate the command, for
example 'Al'. But you can also abbreviate the command options and the '=' is
optional with the ``--spaces`` option. Also, options can be mixed up with
arguments, so the following commands are equivalent.

.. code-block: vim

    1,3 Align --spaces=1 --right =
    1,3 Al --spaces=1 --right =
    1,3 Al --s=1 --r =
    1,3 Al --s 1 --r =
    1,3 Al = --s 1 --r
    1,3 Al --r 1 --s=1
