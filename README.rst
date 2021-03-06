=====
flint
=====

Flint is a Fortran lint tool.  It is not yet working, but can currently do some
basic tasks.

It is currently written as a Python module, but I expect it will use command
line tools someday.

Flint is not exactly useable at the moment, but it does contain some decent
functionality, and has been integrated into a few projects at a very basic
level.

Currently, tokenization is good, and several very large projects are correctly
tokenized.  But analysis is still rather weak, and would benefit from feedback
from any brave users.


Basic usage
===========

Don't expect much here, but currently one can tokenize and parse the source
code, and it will print an annotated version of the source.

.. code:: python

   from flint.project import Project

   proj = Project(verbose=True)
   proj.parse('path/to/source')

This will stream each tokenized line of source code, preceded by a code
denoting the type of statement (e.g. M for module, D for declaration, etc).
This is mainly for development, but could, for example, be parsed to identify
particular functions or variables.

There is some basic reporting, although no simple or obvious way to present it.
But an example codeblock which can be used to check for trailing whitespace
(denoted as code 'C0102') is shown below.

.. code:: python

   from flint.project import Project

   proj = Project()
   proj.parse('mom6')

   for src in proj.files:
       ws_lines = src.report.errors['C0102']
       if ws_lines:
           print(
               '{fname}: {lineno}'.format(
                   fname=src.path,
                   lineno=', '.join(str(n) for n in ws_lines),
               )
           )

Very few tests exist at the moment, but there is a great deal of opportunity
for improvement here.


Status
======

Flint tokenization is currently quite good.  I describe it below.

The first pass breaks each line into functional tokens, including whitespace.
We also substiute and preprocessor defines.  We check the following:
- Line width
- Trailing whitespace
- Indent
- Whitespace between tokens (but we only check for lengths > 1)
- Letter case (again, somewhat weak)

We then strip the whitespace and save the list of tokens.  The file is saved as
a list of lists of tokens.

These lines are managed by a ``FortLines`` iterator, which primarily handles
line continuations.  It will concatenate additional lines, and will also join
any string continuations.

The second pass then handles

Comments
--------

Strings are tokenized well, delimiters correctly contain the tokens, escaped
delimiters are handled, and line continuations are also respected.  Most of the
ugly cases appear to be working fine.

Preprocessing is handled resonably well.  We make a good effort to respect
``#include`` and ``#define`` statements.  What I don't handle are conditionals,
which can lead to awkward preprocessing of things like ``#ifdef``, which are
largely ignored and are always parsed.

Handling of non-ASCII unicode characters is still a bit wonky.  (Currently only
works for Python 3).



Acknowledgements
================

I want to thank the many authors of hideous, absuive Fortran source code for
improving the robustness of this project.
