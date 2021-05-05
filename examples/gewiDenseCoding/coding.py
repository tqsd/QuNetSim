from qunetsim.objects import Qubit


def dens_encode(q: Qubit, bits: str):
    # assumption: qubit q is entangled with another qubit q' which resides at receiver
    # bits is a two-bit string
    # think of dense_encode as an optical device at the sender side, where each qubit has to pass through the optical device
    # I, X, Y, Z are another way of writing the Pauli matrices

    if bits == '00':
        q.I()
    elif bits == '10':
        q.Z()
    elif bits == '01':
        q.X()
    elif bits == '11':
        q.X()
        q.Z()
    else:
        raise Exception('Bad input')
    return q


def dense_decode(stored_epr_half: Qubit, received_qubit: Qubit):
    received_qubit.cnot(stored_epr_half)
    received_qubit.H()
    meas = [None, None]

    meas[0] = stored_epr_half.measure()
    meas[1] = received_qubit.measure()

    # print('meas-----', meas)

    return str(meas[0]) + str(meas[1])


def encode(q: Qubit, bit: str):
    if bit == "0":
        pass
    elif bit == "1":
        q.X()
    else:
        raise Exception("Bad input")
    return q


def decode(q: Qubit):
    meas = None
    meas = q.measure()
    return str(meas)
