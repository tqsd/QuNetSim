from string import ascii_uppercase, ascii_lowercase
from io import StringIO
from shutil import copyfileobj


def gen_imports():
    imports = StringIO()
    imports.write("from qunetsim.components import Host, Network\n")
    imports.write("from qunetsim.objects import Qubit, Logger\n")
    imports.write("Logger.DISABLED = True\n\n\n")
    imports.seek(0)
    return imports


def gen_protocols():
    content = StringIO()
    content.write("def protocol_1(host, receiver):\n")
    content.write("    # Here we write the protocol code for a host.\n")
    content.write("    for i in range(5):\n")
    content.write("        q = Qubit(host)\n")
    content.write("        q.H()\n")
    content.write("        print('Sending qubit %d.' % (i+1))\n")
    content.write("        host.send_qubit(receiver, q, await_ack=True)\n")
    content.write("        print('Qubit %d was received by %s.' % (i+1, receiver))\n\n\n")

    content.write("def protocol_2(host, sender):\n")
    content.write("    # Here we write the protocol code for another host.\n")
    content.write("    for _ in range(5):\n")
    content.write("        # Wait for a qubit from Alice for 10 seconds.\n")
    content.write("        q = host.get_data_qubit(sender, wait=10)\n")
    content.write("        print('%s received a qubit in the %d state.' % (host.host_id, q.measure()))\n\n\n")
    content.seek(0)
    return content


def gen_main():
    main_content = StringIO()
    main_content.write("def main():\n")
    main_content.write("   network = Network.get_instance()\n")
    num_nodes = int(input("How many nodes are in the network? "))
    nodes = []

    node_names = list(ascii_uppercase)
    node_names.extend(ascii_lowercase)

    if (num_nodes > len(node_names)):
        print('Please use less than %d nodes' % len(num_nodes))

    for i in range(num_nodes):
        nodes.append(node_names[i])
    main_content.write("   nodes = " + str(nodes) + "\n")
    main_content.write("   network.start(nodes)\n\n")
    for n in nodes:
        main_content.write("   host_" + n + " = Host('" + n + "')\n")
        for m in nodes:
            if m != n:
                main_content.write("   host_" + n + ".add_connection('" + m + "')\n")

        main_content.write("   host_" + n + ".start()\n")
    main_content.write("\n")
    for n in nodes:
        main_content.write("   network.add_host(host_" + n + ") \n")

    main_content.write("\n")
    main_content.write("   t1 = host_" + nodes[0] + ".run_protocol(protocol_1, (host_" \
                    + nodes[-1] + ".host_id,))\n")
    main_content.write("   t2 = host_" + nodes[-1] + ".run_protocol(protocol_2, (host_" \
                    + nodes[0] + ".host_id,))\n")
    main_content.write("   t1.join()\n")
    main_content.write("   t2.join()\n")
    main_content.write("   network.stop(True)\n\n")
    main_content.seek(0)
    return main_content


if __name__ == '__main__':
    file_name = input("File name? (exclude file type (i.e. don't put .py)): ")
    if file_name == "":
        print("File name must not be empty.")
    else:
        file_closing = StringIO()
        file_closing.write("if __name__ == '__main__':\n")
        file_closing.write("   main()\n")
        file_closing.seek(0)
        with open(file_name + '.py', 'w') as f:
            copyfileobj(gen_imports(), f)
            copyfileobj(gen_protocols(), f)
            copyfileobj(gen_main(), f)
            copyfileobj(file_closing, f)
