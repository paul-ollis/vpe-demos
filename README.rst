Some Vim Python Extensions (VPE) demos
======================================

NOTE: In order to use any of the code here, you will need to install VPE. See:

    https://www.vim.org/scripts/script.php?script_id=5905

You should use version 0.7.2 or newer of VPE.

There is only a small number of examples so far. I plan to add more over time.
I would be very happy to receive suggestions:

- Specific example ideas.
- Parts of the VPE API that you feel urgently need examples.

Please make suggestions using the VPE issue tracker:

    https://github.com/paul-ollis/vim-vpe/issues


Introduction
------------

This directory tree contains various demonstrations of how you can use VPE. All
of the code in here has undergone some far-from-vigorous testing.

The point of the code here is to provide code that you can run and experiment
with as a way to get familiar with the VPE library. Some of the things the
examples aim for are:

- To help learn how to use VPE.
- To provide additional information in a form that is less dry than the docs
  at https://vim-vpe.readthedocs.io/en/latest/index.html
- Be a resource of working code examples.
- Aim for readability over performance.
- Aim to explain, so the code may have more comments than you might otherwise
  expect.

Some non-aims are:

- The examples do not aim to show the "best" way do do things. Some examples
  might (for example) be a bit inefficient.
- Few of the examples aim to be especially useful, other than as a teaching aid
  for VPE.


Contents
--------

This directory contains a number of sub-directories:

VPE-newbies
    This directory provides introductory (including some important) information
    such as:

    - How to redirect Python print() output to the VPE log, which is
      generally a more pleasant setup when developing Python code for Vim.

    - How to show the VPE log.

    This has a number (well only one at the moment) of very short textual, Vim
    and Python scripts. Each has a name of the form ``demo-NN-<name>.vim``,
    ``demo-NN-<name> or ``demo-NN[name.rst`` where NN is 01, 02, *etc*. The
    numbers provide a suggested order to view/run them in.

    The textual (rst) files are very short tutorials, which invite you to try
    things using Vim command (:) prompt.

utilities
    Various small utility scripts.

    Currently this just contains a simple buffer switcher.

toys
    Scripts that are basically toys.

    Currently this just contains a Tower of Hanoi animation.

align
    This provides an example that is structured as a VPE managed plugin.


.. vim: nospell
