Windows
-------

#) Download / Clone the `Git repository`_.

    #) :code:`git clone git@github.com:tqsd/QuNetSim.git`

#) Here we use a Python `virtual environment`_ located at the same directory level as where the project is cloned. Instructions for setting this up:

    #) :code:`python3 -m venv venv`
    #) :code:`.\venv\Scripts\activate`
    #) :code:`pip install --upgrade pip`
    #) :code:`pip install -r .\QuNetSim\requirements.txt`

#) To set the correct path run:

    #) :code:`export PYTHONPATH=$PYTHONPATH:$PWD/QuNetSim/`

#) After installing, you can use the templating script to get started. It will generate a file with the common structure of a QuNetSim use.

    #) :code:`python3 .\QuNetSim\templater.py`
    #) The template will perform a small example which can be run:
       :code:`python3 <name of your file>.py`

.. _Git repository: https://github.com/tqsd/QuNetSim
.. _virtual environment: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/
