Linux / Mac OS X
----------------

#) Make sure you have python 3.5 or greater. For Mac OS users, one should have terminal commands installed.
#) Download / Clone the `Git repositiory`_.

    #) :code:`git clone git@github.com:tqsd/QuNetSim.git`

#) Here we use a Python `virtual environment`_ located at the same directory level as where the project is cloned. Instructions for setting this up:

    #) :code:`python3 -m venv venv`
    #) :code:`source ./venv/bin/activate`
    #) :code:`pip install -r ./QuNetSim/requirements.txt`

#) To set the correct path run:

    #) :code:`export PYTHONPATH=$PYTHONPATH:$PWD`

#) After installing, you can use the templating script to get started. It will generate a file with the common structure of a QuNetSim use.

    #) :code:`python3 ./QuNetSim/templater.py`
    #) The template will perform a small example which can be run:
       :code:`python3 <name of your file>.py`

.. _Git repositiory: https://github.com/tqsd/QuNetSim
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
