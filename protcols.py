def teleport(Sender, receiver, q):
    qA = Sender.createEPR(receiver)
    q.cnot(qA)
    q.H()
    a = q.measure()
    b = qA.measure()
    Sender.sendClassical(receiver, [a, b])


def receive_teleport(Receiver):
    qB = Receiver.recvEPR()
    data = Receiver.recvClassical()
    message = list(data)
    a = message[0]
    b = message[1]

    # Apply corrections
    if b == 1:
        qB.X()
    if a == 1:
        qB.Z()

    return qB
