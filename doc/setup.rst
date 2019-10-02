Setup
=====

The shell variable :envvar:`ELOG_PATH` should be defined:

.. code-block:: bash

    export ELOG_PATH=/your/favorite/elog/path

Remove and download the setup script to ensure you have the most up-to-date
version:

.. code-block:: bash

    rm -f setup_gemdaq.sh
    wget https://raw.githubusercontent.com/cms-gem-daq-project/sw_utils/master/scripts/setup_gemdaq.sh

Then execute:

.. code-block:: bash

    source setup_gemdaq.sh -c <cmsgemos tag> -g <gem-plotting tag> -G <gem-plotting dev version optional>

Tags for each of the repo's can be found:

* `cmsgemos <https://github.com/cms-gem-daq-project/cmsgemos/tags>`_ version
  X.Y.Z (``-c X.Y.Z``)
* `gemplotting <https://github.com/cms-gem-daq-project/gem-plotting-tools/tags>`_
  version X.Y.Z-devA (``-g X.Y.Z -G A``)
* `vfatqc <https://github.com/cms-gem-daq-project/vfatqc-python-scripts/tags>`_
  version X.Y.Z-devA (``-g X.Y.Z -G A``)

Where ``X``, ``Y``, ``Z``, and ``A`` are integers, and most likely will be
different for each of the repositories. If a development version is not to be
used (normal case), you can drop the ``-G`` option. If this is the first time
you are executing the above command, it will create a Python ``virtualenv`` for
you and install the ``cmsgemos``, ``gemplotting``, and ``vfatqc`` packages. It may take some
time to download them, so be patient and do not interrupt the installation.

.. admonition:: Example
    :class: note

    .. code-block:: bash

        source setup_gemdaq.sh -c 0.3.1 -g 1.0.0 -G 5

    This command will install the following packages:

    * `cmsgemos <https://github.com/cms-gem-daq-project/cmsgemos/tags>`_ version
      0.3.1 (``-c 0.3.1``)
    * `gemplotting <https://github.com/cms-gem-daq-project/gem-plotting-tools/tags>`_
      version 1.0.0-dev5 (``-g 1.0.0 -G 5``)
    * `vfatqc <https://github.com/cms-gem-daq-project/vfatqc-python-scripts/tags>`_
      version 1.0.0-dev7 (``-g 1.0.0 -G 7``)

In addition to installing the dependencies, the script will try to guess
:envvar:`DATA_PATH` based on the machine you are using.

To disable the python env execute:

.. code-block:: bash

    deactivate

To re-enable the python env, source the script again:

.. code-block:: bash

    source setup_gemdaq.sh

Note that you should always source the setup script from the same directory.
