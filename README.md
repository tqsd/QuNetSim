Defaultly, Simulaqron can simulate only 10 qubit at a time. We need more than 10 qubits for some simulations in our repository so we need to change that in the source code of Simulaqron. To do so :

1-Go to ./lib/python3.6/site-packages/simulaqron/virtNode/basics.py
2- Change the init function 

from :

def __init__(self, node, num, maxQubits=10):

to : 

def __init__(self, node, num, maxQubits=15):


