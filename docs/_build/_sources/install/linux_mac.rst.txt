1) Make sure you have python 3.5 or greater. For Mac OS users, one should have terminal commands installed.

2) Download / Clone the `Git repository`_.

    1) :code:`git clone git@github.com:tqsd/QuNetSim.git`

3) Here we use a Python `virtual environment`_ located at the same directory level as where the project is cloned (i.e. dont change directories after running step 1). Instructions for setting this up:

    1) :code:`python3 -m venv venv`
    2) :code:`source ./venv/bin/activate`
    3) :code:`pip install --upgrade pip`
    4) :code:`pip install -r ./QuNetSim/requirements.txt`


.. note::
    We include ProjectQ as a standard package which may not install properly without a C++ compiler. See ProjectQ
    documentation for how to install ProjectQ with just the Python version. Alternatively, you can edit the
    :code:`requirements.txt` file and remove the ProjectQ requirement since it is optional. The issue can be resolved in
    most cases by running :code:`pip install projectq --global-option=--without-cppsimulator` and then running step 4
    above again, but this will only install the ProjectQ Python simulator, and not the C version.



4) To set the correct Python path run:

    1) :code:`export PYTHONPATH=$PYTHONPATH:$PWD/QuNetSim/`

5) After installing, you can use the templating script to get started. It will generate a file with the common structure of a QuNetSim use.

    1) :code:`python3 ./QuNetSim/templater.py`
    2) The template will perform a small example which can be run:
       :code:`python3 <name of your file>.py`

.. _Git repository: https://github.com/tqsd/QuNetSim
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
