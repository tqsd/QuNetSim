from string import ascii_uppercase
import subprocess
import os


def gen_imports():
    imports = ""
    imports += "from components.host import Host\n"
    imports += "from components.network import Network\n"
    imports += "from objects.qubit import Qubit\n"
    imports += "import time\n\n"
    return imports


def gen_protocols():
    content = ""
    content += "def protocol_1(host, receiver):" + "\n"
    content += "    " + "# Here we write the protocol code for a host.\n"
    content += "    " + "host.send_classical(receiver, 'Hello!', await_ack=True)\n"
    content += "    " + "print('Message was received')" + "\n\n"

    content += "def protocol_2(host):" + "\n"
    content += "    " + "# Here we write the protocol code for another host.\n\n"
    content += "    " + "# Keep checking for classical messages for 10 seconds.\n"
    content += "    " + "for _ in range(10):" + "\n"
    content += "        " + "time.sleep(1)" + "\n"
    content += "        " + "print(host.classical[0].content)" + "\n\n"

    return content


def gen_main():
    main_content = ""
    main_content += "def main():" + "\n"
    main_content += "   " + "network = Network.get_instance()" + "\n"
    num_nodes = int(input("How many nodes are in the network? "))
    nodes = []
    for i in range(num_nodes):
        nodes.append(ascii_uppercase[i])
    main_content += "   " + "nodes = " + str(nodes) + "\n"
    main_content += "   " + "network.start(nodes)" + "\n"
    main_content += "\n"
    for n in nodes:
        main_content += "   " + "host_" + n + " = Host('" + n + "')" + "\n"
        for m in nodes:
            if m != n:
                main_content += "   " + "host_" + n + ".add_connection('" + m + "')" + "\n"

        main_content += "   " + "host_" + n + ".start()" + "\n"
    main_content += "\n"
    for n in nodes:
        main_content += "   network.add_host(" + "host_" + n + ") \n"

    main_content += "\n"
    main_content += "   " + "host_" + nodes[0] + ".run_protocol(protocol_1, (host_" \
                    + nodes[-1] + ".host_id,))\n"
    main_content += "   " + "host_" + nodes[-1] + ".run_protocol(protocol_2, ())\n\n"
    return main_content


if __name__ == '__main__':
    file_name = input("File name? (exclude file type (i.e. don't put .py)): ")
    if file_name == "":
        print("File name must not be empty.")
    else:
        file_content = gen_imports()
        file_content += gen_protocols()
        file_content += gen_main()
        file_content += "if __name__ == '__main__':\n"
        file_content += "   main()\n"
        f = open(file_name + '.py', 'w')
        f.write(file_content)
