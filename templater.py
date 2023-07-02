from io import StringIO
from shutil import copyfileobj
from pathvalidate import ValidationError, validate_filename
from string import ascii_uppercase, ascii_lowercase
from qunetsim.components import Network

backends = {
    1: {'name': 'EQSN', 'import': 'EQSNBackend'},
    2: {'name': 'CQC', 'import': 'CQCBackend'},
    3: {'name': 'QuTip', 'import': 'QuTipBackend'},
    4: {'name': 'ProjectQ', 'import': 'ProjectQBackend'},
}

topologies = dict()
for i in range(0, len(Network.topologies)):
    topologies[i + 1] = list(Network.topologies.keys())[i]


def prompt_valid_filename() -> str:
    valid_filename = False
    while not valid_filename:
        file_name = input("Name for this template (default: template): ")
        if file_name == "":
            file_name = "template.py"
            valid_filename = True
        else:
            try:
                validate_filename(file_name)
                file_name += ".py"
                valid_filename = True
            except ValidationError as e:
                print("----That is an invalid template name.")
                print("----{}".format(e))

    return file_name


def prompt_valid_num() -> int:
    valid_number = False
    while not valid_number:
        num_nodes = input("How many hosts (nodes) are in the network?" +
                          " (default: 3): ")
        if num_nodes == "":
            valid_number = True
            num_nodes = 3
        try:
            if 52 < int(num_nodes):
                print("----This template maker is currently limited to 52 " +
                      "nodes. If this does not meet your needs, please " +
                      "notify the project maintainers.")
            elif int(num_nodes) < 2:
                print("----Please enter a valid integer value.")
            else:
                valid_number = True
                num_nodes = int(num_nodes)
                if num_nodes >= 15:
                    print("---Please be aware simulation performance may " +
                          "suffer with networks larger than around 15 nodes.")
        except ValueError as e:
            print("----Please enter a valid integer value.")

    return num_nodes


def prompt_host_names(num_hosts: int) -> list:
    default_host_names = list(ascii_uppercase) + list(ascii_lowercase)
    host_names = []

    default_check = input("To customize the host names," +
                          " enter any character before pressing " +
                          "enter: ")
    if default_check == "":
        for i in range(0, num_hosts):
            host_names.append(default_host_names[i])
        return host_names

    print(" You have chosen to customize your {} host names."
          .format(num_hosts))

    for i in range(0, num_hosts):
        valid_entry = False
        while not valid_entry:
            host_name = input("Please choose a name for host {} (default: "
                              .format(i + 1) + "{}) : "
                              .format(default_host_names[i]))
            if host_name == "":
                host_name = default_host_names[i]
            elif not host_name.isalnum():
                print("----Please enter a valid host name. Host names must "
                      "consist entirely of alphanumeric values.")
                continue
            if host_name in host_names:
                print("----Please choose a unique host name. This one already"
                      " exists in your network.")
            else:
                valid_entry = True
                host_names.append(host_name)

    return host_names


def prompt_backend() -> int:
    backend_options = {
        i: backends[i]['name'] for i in range(1, len(backends) + 1)
    }
    valid_entry = False
    while not valid_entry:
        print("Your backend options are {}".format(backend_options))
        choice = input("Please enter the number of your desired backend " +
                       "(default: 1): ")
        if choice == "":
            valid_entry = True
            choice = 1
        try:
            if 0 < int(choice) < len(backend_options) + 1:
                valid_entry = True
                choice = int(choice)
            else:
                raise ValueError
        except ValueError as e:
            print("----Please enter a valid number for your choice of " +
                  "backend.")

    return choice


def prompt_topology() -> int:
    valid_entry = False
    while not valid_entry:
        print("Your topology options are {}".format(topologies))
        choice = input("Please enter the number of your desired topology " +
                       "(default: 3): ")
        if choice == "":
            valid_entry = True
            choice = 3
        try:
            if 0 < int(choice) < len(topologies) + 1:
                valid_entry = True
                choice = int(choice)
            else:
                raise ValueError
        except ValueError as e:
            print("----Please enter a valid number for your choice of " +
                  "backend.")
    return choice


# def prompt_eavesdropper(host_names: list) -> str:
#     valid_entry = False
#     decision = False
#     while not valid_entry:
#         choice = input("Would you like to designate one of your hosts " +
#                        "as an eavesdropper? (Default: no) ")
#         if choice == "":
#             choice = "n"
#         try:
#             if choice.lower() == "y" or choice.lower() == "yes":
#                 valid_entry = True
#                 decision = True
#             elif choice.lower() == "n" or choice.lower() == "no":
#                 valid_entry = True
#             else:
#                 raise ValueError
#         except ValueError as e:
#             print("----Please enter a (y)es or (n)o answer.")
#
#     if not decision:
#         return ""
#     else:
#         valid_entry = False
#         host_options = {
#             i + 1: host_names[i] for i in range(0, len(host_names))
#         }
#         while not valid_entry:
#             print("Your hosts are {}".format(host_options))
#             choice = input("Please choose the number of the host which " +
#                            "should be set as an eavesdropper (Default: 1). ")
#             if choice == "":
#                 valid_entry = True
#                 choice = 1
#             try:
#                 if 0 < int(choice) < len(host_options) + 1:
#                     valid_entry = True
#                     choice = int(choice)
#                 else:
#                     raise ValueError
#             except ValueError as e:
#                 print("----Please enter a valid number for your choice of " +
#                       "eavesdropper.")
#         return host_names[choice - 1]


def gen_import_statements(backend_num: int) -> StringIO:
    imports = StringIO()

    imports.write("from qunetsim.components import Host, Network\n")
    imports.write("from qunetsim.objects import Message, Qubit, Logger\n")
    if backend_num != 1:
        imports.write("from qunetsim.backends import " +
                      backends[backend_num]['import'] + '\n')
    imports.write("Logger.DISABLED = True\n\n")
    if backend_num != 1:
        imports.write("# create the " + backends[backend_num]['name'] +
                        " backend object\n")
        imports.write("backend = " + backends[backend_num]['import'] + "()\n\n\n")
    imports.seek(0)
    return imports


def gen_protocols(sniffer_host: str) -> StringIO:
    sniffer_host = sniffer_host.lower()
    protocols = StringIO()
    if sniffer_host != "":
        protocols.write("def " + sniffer_host + "_sniffing_quantum(" +
                        "sender, receiver, qubit):\n")
        protocols.write("    # This is just a sample sniffing protocol\n")
        protocols.write("    # " + sniffer_host.capitalize() + " applies an " +
                        "X operation to all qubits routed through it\n")
        protocols.write("    qubit.X()\n\n\n")
        protocols.write("def " + sniffer_host + "_sniffing_classical(" +
                        "sender, receiver, msg):\n")
        protocols.write("    # This is just a sample sniffing protocol\n")
        protocols.write("    # " + sniffer_host.capitalize() + " modifies " +
                        "the content of all classical messages routed " +
                        "through it\n")
        protocols.write("    if isinstance(msg, Message):\n")
        protocols.write("        msg.content = \"** " +
                        sniffer_host.capitalize() + " was here :) ** \" " +
                        "+ msg.content\n\n\n")
    protocols.write("def protocol_1(host, receiver):\n")
    protocols.write("    # Here we write the protocol code for a host.\n")
    protocols.write("    for i in range(5):\n")
    protocols.write("        s = 'Hi {}.'.format(receiver)\n")
    protocols.write("        print(\"{} sends: {}\"" +
                    ".format(host.host_id, s))\n")
    protocols.write("        host.send_classical(receiver, s," +
                    " await_ack=True)\n")
    protocols.write("    for i in range(5):\n")
    protocols.write("        q = Qubit(host)\n")
    protocols.write("        q.X()\n")
    protocols.write("        print(\"{} sends qubit in the |1> state\"" +
                    ".format(host.host_id))\n")
    protocols.write("        host.send_qubit(receiver, q, " +
                    "await_ack=True)\n\n\n")
    protocols.write("def protocol_2(host, sender):\n")
    protocols.write("    # Here we write the protocol code for another host." +
                    "\n")
    protocols.write("    for i in range(5):\n")
    protocols.write("        sender_message = host.get_classical(sender, " +
                    "wait=5, seq_num=i)\n")
    protocols.write("        print(\"{} Received classical: {}\"" +
                    ".format(host.host_id, sender_message.content))\n")
    protocols.write("    for i in range(5):\n")
    protocols.write("        q = host.get_qubit(sender, wait=10)\n")
    protocols.write("        m = q.measure()\n")
    protocols.write("        print(\"{} measured: {}\"" +
                    ".format(host.host_id, m))\n\n\n")
    protocols.seek(0)
    return protocols


def gen_main(topology: int, host_names: list) -> StringIO:
    main_content = StringIO()
    main_content.write("def main():\n")
    main_content.write("    network = Network.get_instance()\n")
    main_content.write("    nodes = " + str(host_names) + "\n")
    main_content.write("    network.generate_topology(nodes, \'" +
                       topologies[topology] + "\')\n")
    main_content.write("    network.start(nodes)\n\n")
    for n in host_names:
        main_content.write("    host_" + n.lower() + " = network.get_host(\'"
                           + n + "\')\n")
    main_content.write("\n")
    main_content.seek(0)
    return main_content


def gen_eavesdropper(eavesdropping_host_name: str) -> StringIO:
    sniffer_content = StringIO()

    if eavesdropping_host_name == "":
        return sniffer_content

    sniffer_host = "host_" + eavesdropping_host_name.lower()
    sniffer_content.write("    " + sniffer_host +
                          ".quantum_relay_sniffing = True\n")
    sniffer_content.write("    " + sniffer_host +
                          ".quantum_relay_sniffing_function = " +
                          eavesdropping_host_name.lower() +
                          "_sniffing_quantum\n\n")
    sniffer_content.write("    " + sniffer_host +
                          ".relay_sniffing = True\n")
    sniffer_content.write("    " + sniffer_host +
                          ".relay_sniffing_function = " +
                          eavesdropping_host_name.lower() +
                          "_sniffing_classical\n\n")
    sniffer_content.seek(0)
    return sniffer_content


def gen_run(host_names: list) -> StringIO:
    main_run = StringIO()
    main_run.write("    t1 = host_" + host_names[0].lower() +
                   ".run_protocol(protocol_1, (host_" +
                   host_names[-1].lower() + ".host_id,))\n")
    main_run.write("    t2 = host_" + host_names[-1].lower() +
                   ".run_protocol(protocol_2, (host_" +
                   host_names[0].lower() + ".host_id,), blocking=True)\n")
    main_run.write("    network.stop(True)\n\n\n")
    main_run.seek(0)
    return main_run


if __name__ == '__main__':
    file_name = prompt_valid_filename()
    num_nodes = prompt_valid_num()
    host_names = prompt_host_names(num_nodes)
    back_end = prompt_backend()
    topology = prompt_topology()
    # eavesdropper = prompt_eavesdropper(host_names)
    eavesdropper = ""
    file_closing = StringIO()
    file_closing.write("if __name__ == '__main__':\n")
    file_closing.write("    main()\n")
    file_closing.seek(0)
    with open(file_name, 'w') as f:
        copyfileobj(gen_import_statements(back_end), f)
        copyfileobj(gen_protocols(eavesdropper), f)
        copyfileobj(gen_main(topology, host_names), f)
        copyfileobj(gen_eavesdropper(eavesdropper), f)
        copyfileobj(gen_run(host_names), f)
        copyfileobj(file_closing, f)
