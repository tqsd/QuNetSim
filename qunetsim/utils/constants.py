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

    # DATA KINDS
    SIGNAL = 'signal'
    CLASSICAL = 'classical'
    QUANTUM = 'quantum'

    # SIGNALS
    ACK = 'qunetsim_ACK__'
    NACK = 'qunetsim_NACK__'

    # PROTOCOL IDs
    REC_EPR = 'rec_epr'
    SEND_EPR = 'send_epr'
    REC_TELEPORT = 'rec_teleport'
    SEND_TELEPORT = 'send_teleport'
    REC_SUPERDENSE = 'rec_superdense'
    SEND_SUPERDENSE = 'send_superdense'
    REC_CLASSICAL = 'rec_classical'
    SEND_CLASSICAL = 'send_classical'
    SEND_BROADCAST = 'send_broadcast'
    RELAY = 'relay'
    SEND_QUBIT = 'send_qubit'
    REC_QUBIT = 'rec_qubit'
    SEND_KEY = 'send_key'
    REC_KEY = 'rec_key'
    SEND_GHZ = 'send_ghz'
    REC_GHZ = 'rec_ghz'

    # MISC
    QUBITS = 'qubits'
    HOSTS = 'hosts'
    KEYSIZE = 'keysize'
