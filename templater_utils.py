from string import ascii_uppercase, ascii_lowercase
from io import StringIO
from pathvalidate import ValidationError, validate_filename


def gen_main(host_names: list) -> StringIO:
    main_content = StringIO()
    main_content.write("def main():\n")
    main_content.write("   network = Network.get_instance()\n")

    node_names = list(ascii_uppercase)
    node_names.extend(ascii_lowercase)

    main_content.write("   nodes = " + str(host_names) + "\n")
    main_content.write("   network.start(nodes)\n\n")
    for n in host_names:
        main_content.write("   host_" + n + " = Host('" + n + "')\n")
        for m in host_names:
            if m != n:
                main_content.write("   host_" + n + ".add_connection('" + m + "')\n")

        main_content.write("   host_" + n + ".start()\n")
    main_content.write("\n")
    for n in host_names:
        main_content.write("   network.add_host(host_" + n + ") \n")

    main_content.write("\n")
    main_content.write("   t1 = host_" + host_names[0] + ".run_protocol(protocol_1, (host_" \
                    + host_names[-1] + ".host_id,))\n")
    main_content.write("   t2 = host_" + host_names[-1] + ".run_protocol(protocol_2, (host_" \
                    + host_names[0] + ".host_id,))\n")
    main_content.write("   t1.join()\n")
    main_content.write("   t2.join()\n")
    main_content.write("   network.stop(True)\n\n")
    main_content.seek(0)
    return main_content


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


def get_valid_num() -> int:
    valid_number = False
    while not valid_number:
        num_nodes = input("How many hosts (nodes) are in the network?" +
                          "(Default: 3): ")
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


def get_valid_filename() -> str:
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


def get_host_names(num_hosts: int) -> list:
    default_host_names = list(ascii_uppercase) + list(ascii_lowercase)
    host_names = []

    default_check = input("If you would like to customize your host names," +
                          " please enter any character before pressing enter.")
    if default_check == "":
        for i in range(0, num_hosts):
            host_names.append(default_host_names[i])
        return host_names

    print(" You have chosen to customize your {} host names."
          .format(num_hosts))

    for i in range(0, num_hosts):
        valid_entry = False
        while not valid_entry:
            host_name = input("Please choose a name for host {} (Default: "
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
