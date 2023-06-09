#################
Development guide
#################

This page provides procedures and guidelines for developing and contributing to Squarebot.

Scope of contributions
======================

Squarebot is an open source package, meaning that you can contribute to Squarebot itself, or fork Squarebot for your own purposes.

Since Squarebot is intended for internal use by Rubin Observatory, community contributions can only be accepted if they align with Rubin Observatory's aims.
For that reason, it's a good idea to propose changes with a new `GitHub issue`_ before investing time in making a pull request.

Squarebot is developed by the Rubin Observatory SQuaRE team.

.. _GitHub issue: https://github.com/lsst-sqre/squarebot/issues/new

.. _dev-environment:

Setting up a local development environment
==========================================

Squarebot is a Python project that should be developed within a virtual environment.
The easiest way to set up a development environment is to run Nox_ from a local clone of squarebot:

.. code-block:: sh

   git clone https://github.com/lsst-sqre/squarebot.git
   cd squarebot
   pip install nox
   nox -s init-dev
   source .venv/bin/activate

This init step does three things:

1. Creates a `venv`_ virtual environment in the ``.venv`` subdirectory.
2. Installs Squarebot along with its runtime and development dependencies.
3. Installs the pre-commit hooks.

Whenever you return to the project in a new shell you will need to activate the virtual environment:

.. code-block:: sh

   source .venv/bin/activate

.. _pre-commit-hooks:

Pre-commit hooks
================

The pre-commit hooks, which are automatically installed by running the :command:`nox -s init-dev` command on :ref:`set up <dev-environment>`, ensure that files are valid and properly formatted.
Some pre-commit hooks automatically reformat code:

``isort``
    Sorts Python imports.

``black``
    Automatically formats Python code.

When these hooks fail, your Git commit will be aborted.
To proceed, stage the new modifications and proceed with your Git commit.

.. _dev-run-tests:

Running tests
=============

To test all components of Squarebot, run nox_, which tests the library the same way that the GitHub Actions CI workflow does:

.. code-block:: sh

   nox

To see a listing of specific nox sessions, run:

.. code-block:: sh

   nox -s

Building documentation
======================

Documentation is built with Sphinx_:

.. _Sphinx: https://www.sphinx-doc.org/en/master/

.. code-block:: sh

   nox -s docs

The build documentation is located in the :file:`docs/_build/html` directory.

To check the documentation for broken links, run:

.. code-block:: sh

   nox -s docs-linkcheck

.. _dev-change-log:

Updating the change log
=======================

Squarebot uses scriv_ to maintain its change log.

When preparing a pull request, run

.. code-block:: sh

   nox -s scriv-create

This will create a change log fragment in :file:`changelog.d`.
Edit that fragment, removing the sections that do not apply and adding entries for your pull request.

Change log entries use the following sections:

- **Backward-incompatible changes**
- **New features**
- **Bug fixes**
- **Other changes** (for minor, patch-level changes that are not bug fixes, such as logging formatting changes or updates to the documentation)

Do not include a change log entry solely for updating pinned dependencies, without any visible change to Squarebot's behavior.
Every release is implicitly assumed to update all pinned dependencies.

These entries will eventually be cut and pasted into the release description for the next release, so the Markdown for the change descriptions must be compatible with GitHub's Markdown conventions for the release description.
Specifically:

- Each bullet point should be entirely on one line, even if it contains multiple sentences.
  This is an exception to the normal documentation convention of a newline after each sentence.
  Unfortunately, GitHub interprets those newlines as hard line breaks, so they would result in an ugly release description.
- Avoid using too much complex markup, such as nested bullet lists, since the formatting in the GitHub release description may not be what you expect and manually editing it is tedious.

.. _style-guide:

Style guide
===========

Code
----

- The code style follows :pep:`8`, though in practice lean on Black and isort to format the code for you. Use :sqr:`072` for for architectural guidance. Use :sqr:`075` for the client-server monorepo architecture and :sqr:`076` for the Pydantic-based Avro schemas.

- Use :pep:`484` type annotations.
  The ``nox -s typing`` test session, which runs mypy_, ensures that the project's types are consistent.

- Write tests for Pytest_.

Documentation
-------------

- Follow the `LSST DM User Documentation Style Guide`_, which is primarily based on the `Google Developer Style Guide`_.

- Document the Python API with numpydoc-formatted docstrings.
  See the `LSST DM Docstring Style Guide`_.

- Follow the `LSST DM ReStructuredTextStyle Guide`_.
  In particular, ensure that prose is written **one-sentence-per-line** for better Git diffs.

.. _`LSST DM User Documentation Style Guide`: https://developer.lsst.io/user-docs/index.html
.. _`Google Developer Style Guide`: https://developers.google.com/style/
.. _`LSST DM Docstring Style Guide`: https://developer.lsst.io/python/style.html
.. _`LSST DM ReStructuredTextStyle Guide`: https://developer.lsst.io/restructuredtext/style.html
