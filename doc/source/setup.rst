.. _vfaqc-setup:

=====
Setup
=====


Installation
------------

Installation of the ``gempython_vfatqc`` package can be accomplished one of two ways:
* Installation into the system with ``yum`` (see :ref:`expertguide:gemos-sw-yum-installation`)
* Installation into a local python virtual environment (see :ref:`expertguide:gemos-installation-pip`)


Environment
-----------

A number of shell variables should be defined:

+--------------------------+----------------------------------------------------+
| Variable name            | Description                                        |
+==========================+====================================================+
| :envvar:`ELOG_PATH`      | Location the software will place certain plots     |
+--------------------------+----------------------------------------------------+
| :envvar:`DATA_PATH`      | Location the software will place output files      |
|                          | and will look for intermediate results             |
+--------------------------+----------------------------------------------------+
| :envvar:`GBT_SETTINGS`   | Location the software will look for GBTx           |
|                          | configuration settings                             |
+--------------------------+----------------------------------------------------+


.. code-block:: bash

    export ELOG_PATH=/your/favorite/elog/path
    export DATA_PATH=/your/favourite/output/path
    export GBT_SETTINGS=/your/favourite/gbt/settings/path

