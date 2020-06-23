[![Unitary Fund](https://img.shields.io/badge/Supported%20By-UNITARY%20FUND-brightgreen.svg?style=for-the-badge)](http://unitary.fund)
# QuNetSim 

![QuNetSim Tests](https://github.com/tqsd/QuNetSim/workflows/QuNetSim%20Tests/badge.svg)

QuNetSim is a quantum-enabled network simulator that adds common quantum networking tasks like teleportation, superdense coding, sharing EPR pairs, etc. With QuNetSim, one can design and test robust quantum network protocols under various network conditions.

## Installation and Documentation

See https://tqsd.github.io/QuNetSim/ for documentation. To install the latest release via pip:
```
pip install qunetsim
```

## Quick Start Guide

### Templater

The QuNetSim pip package comes with a templater. After installing the library, simply type `template` and follow the instructions. A template QuNetSim example will be generated. 

### Quick Example

```
from qunetsim.components import Host, Network

network = Network.get_instance()
network.start()

alice = Host('Alice')
bob = Host('Bob')

alice.add_connection(bob.host_id)
bob.add_connection(alice.host_id)

alice.start()
bob.start()

network.add_hosts([alice, bob])

# Block Alice to wait for qubit arrive from Bob
alice.send_epr(bob.host_id, await_ack=True)
q_alice = alice.get_epr(bob.host_id)
q_bob = bob.get_epr(alice.host_id)

print("EPR is in state: %d, %d" % (q_alice.measure(), q_bob.measure()))
network.stop(True)
```

## Contributing 

Feel free to contribute by adding Github issues and pull requests. Adding test cases for any contributions is a requirement for any pull request to be merged. 
