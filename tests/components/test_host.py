from components.host import Host
from random import randint


def test_connections():
    print("Start connection test...")
    name = "A"
    neighbor = [str(x) for x in range(10)]
    a = Host(name)
    for x in neighbor:
        a.add_connection(x)

    list = a.get_connections()
    for i in list:
        assert i['connection'] in neighbor
    print("test succefull!")
    a.backend.stop()


def test_sequence_numbers():
    print("Start sequence number test...")
    a = Host('A')
    neighbor = [str(x) for x in range(10)]
    random = [randint(0, 200) for _ in range(10)]
    for n, i in zip(neighbor, random):
        for _ in range(i):
            _ = a._get_sequence_number(n)

    for n, i in zip(neighbor, random):
        assert i == a._get_sequence_number(n)

    print("test succefull!")
    a.backend.stop()


if __name__ == '__main__':
    test_connections()
    test_sequence_numbers()
    exit(0)
