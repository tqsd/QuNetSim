#) Make sure you have python 3.5 or greater. For Mac OS users, one should have terminal commands installed.

#) Download / Clone the `Git repository`_.

    #) :code:`git clone git@github.com:tqsd/QuNetSim.git`

#) Here we use a Python `virtual environment`_ located at the same directory level as where the project is cloned (i.e. dont
change directories after running step 1). Instructions for setting this up:

    #) :code:`python3 -m venv venv`
    #) :code:`source ./venv/bin/activate`
    #) :code:`pip install --upgrade pip`
    #) :code:`pip install -r ./QuNetSim/requirements.txt`

.. note::
    We include ProjectQ as a standard package which may not install properly without a C++ compiler. See ProjectQ
    documentation for how to install ProjectQ with just the Python version. Alternatively, you can edit the
    :code:`requirements.txt` file and remove the ProjectQ requirement since it is optional.


#) To set the correct Python path run:

    #) :code:`export PYTHONPATH=$PYTHONPATH:$PWD/QuNetSim/`

#) After installing, you can use the templating script to get started. It will generate a file with the common structure of a QuNetSim use.

    #) :code:`python3 ./QuNetSim/templater.py`
    #) The template will perform a small example which can be run:
       :code:`python3 <name of your file>.py`

.. _Git repository: https://github.com/tqsd/QuNetSim
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
