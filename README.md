[![Unitary Fund](https://img.shields.io/badge/Supported%20By-UNITARY%20FUND-brightgreen.svg?style=for-the-badge)](http://unitary.fund)

# QuNetSim

QuNetSim is a quantum-enabled network simulator that adds common quantum networking tasks like teleportation, superdense coding, sharing EPR pairs, etc. With QuNetSim, one can design and test robust classical-quantum network protocols under various network conditions.

Open docs/index.html in a browser for documentation (still under construction, but some points are there).

## SETUP INSTRUCTIONS

##### Install Python 3.6:

Debian/Ubuntu:

`sudo apt-get install python3`

Windows:

https://www.python.org/downloads/

##### Install python3 virtual environments:

Debian/Ubuntu:

`sudo apt-get install python3-venv`

Windows:

Find out where your python resides using 'where python' command in CMD
Then follow this guide: https://www.c-sharpcorner.com/article/steps-to-set-up-a-virtual-environment-for-python-development/


##### Clone the project:

`git clone <url>`

#### At the same level as the cloned directory, create a virtual environment with the following:

To create:

`python3 -m venv venv`

To start:

Debian/Ubuntu:

`source venv/bin/activate`

Windows:
`.\venv\Scripts\activate`

#### In the cloned directory (i.e. cd QuNetSim) install the python libraries:
To install packages in requirements.txt:

`pip install -r requirements.txt`

To stop the virtual environment (when not using the code) run:

`deactivate`
