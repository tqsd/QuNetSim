1) Make sure you have python 3.5 or greater.

2) Download / Clone the `Git repository`_.

    1) :code:`git clone git@github.com:tqsd/QuNetSim.git`

3) Here we use a Python `virtual environment`_ located at the same directory level as where the project is cloned (i.e. dont change directories after running step 1). Instructions for setting this up:

    #) :code:`python3 -m venv venv`
    #) :code:`.\venv\Scripts\activate`
    #) :code:`python -m pip install --upgrade pip`
    #) :code:`python -m pip install -r .\QuNetSim\requirements.txt`


.. note::
    We include ProjectQ as a standard package which may not install properly without a C++ compiler. See ProjectQ
    documentation for how to install ProjectQ with just the Python version. Alternatively, you can edit the
    :code:`requirements.txt` file and remove the ProjectQ requirement since it is optional. The issue can be resolved in
    most cases by running :code:`pip install projectq --global-option=--without-cppsimulator` and then running step 4
    above again, but this will only install the ProjectQ Python simulator, and not the C version.


4) To set the correct Python path we need to set the :code:`PYTHONPATH` system variable:

    #) Open System Properties -> Advanced
    #) Click "Environment Variables"
    #) In the System Variable area (the bottom part)
    #) If the :code:`PYTHONPATH` variable already exists then add :code:`C:\<PATH_TO_QUNETSIM>\QuNetSim` to the path,
       replacing :code:`<PATH_TO_QUNETSIM>` with the path to where QuNetSim is located.
    #) Otherwise, click New and add a variable :code:`PYTHONPATH` with value :code:`C:\<PATH_TO_QUNETSIM>\QuNetSim`,
       replacing :code:`<PATH_TO_QUNETSIM>` with the path to where QuNetSim is located.

5) After installing, you can use the templating script to get started. It will generate a file with the common structure of a QuNetSim use.

    #) :code:`python3 .\QuNetSim\templater.py`
    #) The template will perform a small example which can be run:
       :code:`python3 <name of your file>.py`

.. _Git repository: https://github.com/tqsd/QuNetSim
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
