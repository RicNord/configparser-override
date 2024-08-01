Development
===========

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
    :target: https://pycqa.github.io/isort/
.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
    :target: https://github.com/pre-commit/pre-commit

To list available commands for your convenience:

.. code-block:: shell

    make help

Local environment setup
-----------------------

.. code-block:: shell

    python3 -m venv ./venv
    source ./venv/bin/activate # Linux and MacOS
    venv\Scripts\activate # Windows

    pip install --editable .[dev]

Run tests
---------

.. code-block:: shell

    make pytest # Run pytest
    make style # Run lint formatting and type check
    make test-all # Run all tests with tox

    make auto-fix # Auto-fix possible style issues

Pre-commit hooks
----------------

To install optional `pre-commit <https://pre-commit.com/>`_ hooks; after
environment set-up run:

.. code-block:: bash

    pre-commit install

Project maintenance
====================

Intended for project maintainers

Release
-------

`Bump my version <https://callowayproject.github.io/bump-my-version/>`_ is used
to bump the semantic version of the project.

For details see:

.. code-block:: shell

    bump-my-version bump --help

Bump my version is configured to create a ``new commit`` and ``tag`` it with the
new version when a version is bumped.

When a new tag is pushed to github the
`publish-pypi workflow <./.github/workflows/publish-pypi.yaml>`_ is triggered and
will build and publish the new version to PyPi.

Documentation
-------------

`Sphinx <https://www.sphinx-doc.org/>`_ is used to create documentation for the
project. To generate:

.. code-block:: shell

    cd docs
    make apidocs # Generates API reference documentation for the code of the project
    make html # Generates HTML that can be viewed in the browser
