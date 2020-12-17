class Constants:
    # DATA TYPES
    GENERATE_EPR_IF_NONE = 'generate_epr_if_none'
    AWAIT_ACK = 'await_ack'
    SEQUENCE_NUMBER = 'sequence_number'
    PAYLOAD = 'payload'
    PAYLOAD_TYPE = 'payload_type'
    SENDER = 'sender'
    RECEIVER = 'receiver'
    PROTOCOL = 'protocol'

    KEY = 'key'

    # WAIT TIME
    WAIT_TIME = 10

    # QUBIT TYPES
    EPR = 0
    DATA = 1
    GHZ = 2

    # DATA KINDS
    SIGNAL = 'signal'
    CLASSICAL = 'classical'
    QUANTUM = 'quantum'

    # SIGNALS
    ACK = 'qunetsim_ACK__'
    NACK = 'qunetsim_NACK__'

    # PROTOCOL IDs
    REC_EPR = 1
    SEND_EPR = 2
    REC_TELEPORT = 3
    SEND_TELEPORT = 4
    REC_SUPERDENSE = 5
    SEND_SUPERDENSE = 6
    REC_CLASSICAL = 7
    SEND_CLASSICAL = 8
    SEND_BROADCAST = 9
    RELAY = 10
    SEND_QUBIT = 11
    REC_QUBIT = 12
    SEND_KEY = 13
    REC_KEY = 14
    SEND_GHZ = 15
    REC_GHZ = 16

    # MISC
    QUBITS = 'qubits'
    HOSTS = 'hosts'
    KEYSIZE = 'keysize'
