.. _vfaqc-coding:

======
Coding
======

Coding is done from within your ``virtualenv``, ideally on one of the 904 DAQ
machines; ``lxplus`` is only supported on a *best-effort* basis.
Follow the :doc:`setup instructions <setup>` first. It is recommended that you
use a separate ``virtualenv`` for development.
The instructions below assume that your ``virtualenv`` is created and activated.

First, install the dependencies for development:

.. code-block:: bash

    pip install -r requirements.txt

.. tip::

    In case ``bash`` cannot find ``pip``, try ``python -m pip ...`` instead.

Clone the repository and move to the code directory:

.. code-block:: bash

    git clone --recurse-submodules -b release/legacy git@github.com:cms-gem-daq-project/vfatqc-python-scripts.git
    cd vfatqc-python-scripts


Building and installing
-----------------------

In order to test your code, you need to install it inside your ``virtualenv``.
It is done by building a ``pip`` package:

.. code-block:: bash

    make pip

Once the package is built, it can be installed using:

.. code-block:: bash

    pip install -I rpm/gempython_vfatqc-1.0.0.tar.gz

.. warning::

    This command will *replace* any previously installed version.

Once the package is installed, the tools in :envvar:`PATH` will be replaced by
the version you have checked out, and any new developments will be made
available.

Guidelines
----------

This section includes guidelines that you should do your best to follow while
developing for this project.

Git workflow
............

We have been utilizing a `very helpful guideline`_ for our development model.
The basic idea is the following:

* Fork from ``cms-gem-daq-project/vfatqc-python-scripts``
* Create a branch to develop your particular feature (based off of ``develop``,
  or in some cases, the current release branch)

  * ``hotfix`` may be created from ``master`` if the corresponding fix is also
    applied to ``develop``
  * Once that feature is completed, create a pull request

* ``master`` should always be stable: Do not commit directly onto ``master`` or
  ``develop``, and ensure that your ``master`` and ``develop`` are always
  up-to-date with ``cms-gem-daq-project`` before starting new developments.

* Some generally good guidelines (though this post recommends not using the
  ``git-flow`` model):

  * Never use ``git commit -a``
  * Avoid ``git commit -m`` over ``git commit -p`` or ``git commit``, as it will
    force you to think about your commit message

    * Speaking of... commit messages should be descriptive, not like a novel,
      but concise and complete. If they reference an issue or PR, please include
      that information.

  * Prefer ``git rebase`` over ``git pull`` (or configure ``git pull`` to do a
    rebase)

    * You can set this up either in the repo ``.git/config`` file per repo, or
      per branch, or globally via ``~/.gitconfig``
    * `Golden rebase rules`_

      * Executive summary: never rebase a public branch, i.e., a branch you have
        pushed somewhere, and especially not a branch that others may be
        collaborating with

Coding Style
............

* Avoid using tabs, use an editor that is smart enough to convert all tabs to
  spaces
* Current convention is 4 spaces per tab for python and C++ code
* Every externally visible entity *must* be documented
* Python scripts should have an extensive module-level docstring describing, at
  the minimum:

  * The calling syntax ("Synopsis" section)
  * A description of what the script does
  * The list of all arguments
  * A list of relevant environment variable, and an explanation of how they
    influence the behaviour of the script

  Adding a comprehensive set of examples is strongly encouraged but not
  mandatory.

* Documentation of Python code should follow the `Google style`_

Testing
.......

* You should, at a minimum, test that your code interprets properly, and if
  possible, test that it runs without crashing
* When testing, you should set up a ``virtualenv`` and use ``pip`` to install
  the package.
* If you also need to test this against other ``gempython`` packages
  (``cmsgemos``, ``gem-plotting-tools``), you should find the release that is compatible
  from the releases page of the repository and use ``pip`` to install them into
  your ``virtualenv``
* If you updated the documentation, you should at least produce the HTML version
  and check it in a Web browser (NOT lynx). Checking the ``man`` pages is
  encouraged.

Documentation
-------------

This project is documented using `Sphinx`_. Once the package has been installed
in your ``virtualenv``, the documentation can be built using:

.. code-block:: bash

    make html

This will create a tree of static HTML Web pages under ``doc/_build/html``. They
can be viewed from within the terminal using `lynx`_:

.. code-block:: bash

    lynx doc/_build/html/index.html

It is also possible to create standard ``man`` pages using:

.. code-block:: bash

    make man

They are located in ``doc/_build/man`` and can be viewed using ``man <FILE>``.

.. note::

    ``make html`` may fail to update the documentation after you run
    ``make man``. If this happens, run ``make cleandoc`` to restart from
    scratch.

.. note::

    When modifying documentation located in Python modules, you should make a
    new ``pip`` package and install it before running ``make html`` or
    ``make man``.

Writing documentation
.....................

The documentation uses Restructured Text. It should be easy to learn if you
already know Markdown, but it is much more powerful. Here are some useful links
to get you started, in no particular order:

  * https://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html
  * http://www.sphinx-doc.org/en/stable/markup/para.html

The structure of the documentation is created by hand using ``.rst`` files
located in the ``doc`` folder. ``man`` pages are created from files located in
``doc/man`` and must be listed in ``doc/conf.py`` to be generated.

Cross-referencing (links *within* the documentation) is achieved using so-called
*roles*. A role specifies the kind of resource that the link should point to (Is
it a Python function? A module? A documentation page?) The list of roles used to
document Python code can be found
`here <http://www.sphinx-doc.org/en/stable/domains.html#python-roles>`_.

Tips
....

* You may sometimes want to use backslashes (\) in your documentation, be it to
  escape some active characters like * or to include LaTeX code (see below).
  When inside a Python docstring, these can be mangled by the interpreter: in
  the following code, "\r" is turned into a carriage return:

  .. code-block:: python

    """I want to say \r"""

  An easy way to avoid this problem is to use "raw" strings:

  .. code-block:: python

    r"""I want to say \r"""

* It's possible to put LaTeX formulas in the documentation. Use them instead of
  fixed-width characters: they are easier to the eye of a physicist. Here's an
  example:

  .. code-block:: rst

    .. math::

        f(x) =
            A \operatorname{erf} \left[
                \frac{\max(x_0, x)-\mu}{\sqrt 2 \sigma}
            \right]
            + B

  This gives:

  .. math::

    f(x) =
        A \operatorname{erf} \left[
            \frac{\max(x_0, x)-\mu}{\sqrt 2 \sigma}
        \right]
        + B

  Did you recognize the S-curve fit function?

.. Link targets

.. _Golden rebase rules: https://www.atlassian.com/git/tutorials/merging-vs-rebasing#the-golden-rule-of-rebasing
.. _Google style: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
.. _lynx: http://lynx.invisible-island.net/
.. _Sphinx: http://www.sphinx-doc.org/en/master/index.html
.. _very helpful guideline: http://nvie.com/posts/a-successful-git-branching-model/
