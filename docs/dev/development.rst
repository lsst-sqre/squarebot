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

Local development requires:

- Python 3.14
- Uv_
- Docker or a compatible container runtime (used by the test suite to run Kafka via testcontainers_)

First, clone the Squarebot repository:

.. code-block:: sh

   git clone https://github.com/lsst-sqre/squarebot.git
   cd squarebot

Squarebot is a uv_ workspace with two packages: the ``squarebot`` server application at the repository root and the published ``rubin-squarebot`` client in :file:`client`.
Set up the development environment, which installs both packages and all dependency groups from the committed :file:`uv.lock` and installs the pre-commit hooks:

.. code-block:: sh

   make init

``make init`` runs ``uv sync --frozen --all-groups`` to create the :file:`.venv` virtual environment and ``pre-commit install`` to set up the Git hooks.
Activate the environment in any shell where you want the ``nox``, ``mypy``, and other tools on your path:

.. code-block:: sh

   source .venv/bin/activate

.. _pre-commit-hooks:

Pre-commit hooks
================

The pre-commit hooks ensure that files are valid and properly formatted.
The hooks are automatically installed by running :command:`make init`.

When these hooks fail, your Git commit will be aborted.
To proceed, stage the new modifications and proceed with your Git commit.

Refer to the :file:`.pre-commit-config.yaml` file for the list of hooks that are run.
You can run the hooks over the whole tree at any time with:

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox -s lint

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox -s lint

.. _dev-run-tests:

Running tests
=============

To test all components of Squarebot, run nox_, which tests the library the same way that the GitHub Actions CI workflow does.
The ``test`` session stands up a Kafka broker with testcontainers_, so Docker must be running, but you do **not** need to start a broker yourself.

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox

File linting, type checking, and unit tests are run as separate nox sessions:

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox -s lint
         nox -s typing
         nox -s test

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox -s lint
         uv run --only-group=nox nox -s typing
         uv run --only-group=nox nox -s test

With the ``test`` session, you can run a specific test file or directory by passing pytest arguments after ``--``:

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox -s test -- tests/handlers/post_message_test.py

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox -s test -- tests/handlers/post_message_test.py

The ``rubin-squarebot`` client has its own test sessions, including compatibility runs against its supported Python versions and a lowest-direct dependency resolution:

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox -s client_test
         nox -s client_test_compat
         nox -s client_test_oldest

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox -s client_test
         uv run --only-group=nox nox -s client_test_compat
         uv run --only-group=nox nox -s client_test_oldest

To see a listing of specific nox sessions, run:

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox --list

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox --list

.. _dev-update-deps:

Updating dependencies
=====================

Pinned dependencies live in the root :file:`uv.lock`.
To upgrade the locked dependencies and the pre-commit hooks, run:

.. code-block:: sh

   make update-deps

To upgrade the dependencies and re-sync your local environment in one step, run ``make update`` (which runs ``make update-deps`` followed by ``make init``).

Building documentation
======================

Documentation is built with Sphinx_:

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox -s docs

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox -s docs

The built documentation is located in the :file:`docs/_build/html` directory.
The ``docs`` session also regenerates the OpenAPI schema by importing the application, so the session sets dummy ``KAFKA_BOOTSTRAP_SERVERS`` and Slack secrets; no running broker is required.

To check the documentation for broken links, run:

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox -s docs-linkcheck

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox -s docs-linkcheck

.. _dev-change-log:

Updating the change log
=======================

Squarebot uses scriv_ to maintain its change log.

When preparing a pull request, run

.. tab-set::

   .. tab-item:: In venv
      :sync: venv

      .. code-block:: sh

         nox -s scriv-create

   .. tab-item:: Without pre-installation
      :sync: uv

      .. code-block:: sh

         uv run --only-group=nox nox -s scriv-create

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

- The code style follows :pep:`8`, though in practice lean on Ruff_ to format the code for you. Use :sqr:`072` for architectural guidance. Use :sqr:`075` for the client-server monorepo architecture and :sqr:`076` for the Pydantic-based Avro schemas.

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
