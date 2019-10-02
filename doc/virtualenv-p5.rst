Setting up a ``virtualenv`` at P5
=================================

Due to the limited Internet access, setting up a ``virtualenv`` at Point 5 is
slightly more involved than on ``lxplus``.

Create a SOCKS proxy that will allow ``pip`` to reach the outer world:

.. code-block:: bash

    PORT=5000
    ssh -D *:$PORT lxplus.cern.ch -N -f

If you get an error saying ``bind: Address already in use``, try with
``PORT=5001``, ``5002``, ...

.. note::

    The proxy expires after some time. Just create it again if ``pip`` complains
    about the network being unreachable.

Define :envvar:`ELOG_PATH`:

.. code-block:: bash

    export ELOG_PATH=/your/favorite/elog/path

Remove and download the setup script to ensure you have the most up-to-date
version:

.. code-block:: bash

    rm -f setup_gemdaq.sh
    ssh cmsusr wget https://raw.githubusercontent.com/cms-gem-daq-project/sw_utils/master/scripts/setup_gemdaq.sh

Then execute:

.. code-block:: bash

    source setup_gemdaq.sh -c <cmsgemos tag> -g <gem-plotting tag> -G <gem-plotting dev version optional> -P $PORT

Tags for each of the repo's can be found:

* `cmsgemos <https://github.com/cms-gem-daq-project/cmsgemos/tags>`_ version
  X.Y.Z (``-c X.Y.Z``)
* `gemplotting <https://github.com/cms-gem-daq-project/gem-plotting-tools/tags>`_
  version X.Y.Z-devA (``-g X.Y.Z -G A``)

Where ``X``, ``Y``, ``Z``, and ``A`` are integers, and most likely will be
different for each of the repositories. If a development version is not to be
used (normal case), you can drop the ``-G`` option. If this is the first time
you are executing the above command, it will create a Python ``virtualenv`` for
you and install the ``cmsgemos`` and ``gemplotting`` packages. It may take some
time to download them, so be patient and do not interrupt the installation.

.. admonition:: Example
    :class: note

    .. code-block:: bash

        source setup_gemdaq.sh -c 0.3.1 -g 1.0.0 -G 5 -P $PORT

    This command will install the following packages:

    * `cmsgemos <https://github.com/cms-gem-daq-project/cmsgemos/tags>`_ version
      0.3.1 (``-c 0.3.1``)
    * `gemplotting <https://github.com/cms-gem-daq-project/gem-plotting-tools/tags>`_
      version 1.0.0-dev5 (``-g 1.0.0 -G 5``)

In addition to installing the dependencies, the script will try to guess
:envvar:`DATA_PATH` based on the machine you are using.

To disable the python env execute:

.. code-block:: bash

    deactivate

To re-enable the python env, source the script again:

.. code-block:: bash

    source setup_gemdaq.sh

Note that you should always source the setup script from the same directory.
