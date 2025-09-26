===========
The VPE log
===========

VPE maintains an internal log, which sometimes provides useful information and
error messages. VPE code can write to this log and you can redirect the output
of the ``print()`` function to the log.

The see the log use the command:
::

    Vpe log show

You can also do this in Python:
::

    py3 vpe.log.show()

While the log is showing, it will automatically scroll when new content is
added.

You can arrange for ``print()`` print output (actually all sys.stdout and
sys.stderr) to go to the log.

    Vpe log redirect on

Now do:
::

    py3 print('This will appear in the log')

You can also get the help for ``Vpe log`` to appear in the log window:
::

    Vpe log --lhelp

This redirection can be a good idea, so you might want to make this your
default setting. To do so, find where the 000-vpe.vim plugin file is. The will
likely be in one these locations:

    $HOME/.vim/plugin
    $HOME/.config/vim/plugin
    $HOME/vimfiles/plugin

And add a file called 001-vpe.vim, containing:
::

    Vpe log redirect on

This will be executed just after the 000-vpe.vim file.

.. vim: nospell
