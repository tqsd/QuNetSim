from io import StringIO
from shutil import copyfileobj
from templater_utils import gen_protocols as gen_protocols
from templater_utils import gen_imports as gen_imports
from templater_utils import gen_main as gen_main
from templater_utils import get_valid_num as get_valid_num
from templater_utils import get_valid_filename as get_valid_filename
from templater_utils import get_host_names as get_host_names
from pathvalidate import ValidationError, validate_filename


if __name__ == '__main__':
    # file_name = get_valid_filename()
    # num_nodes = get_valid_num()
    num_nodes = 3
    host_names = get_host_names(num_nodes)
    print(host_names)

    # file_closing = StringIO()
    # file_closing.write("if __name__ == '__main__':\n")
    # file_closing.write("   main()\n")
    # file_closing.seek(0)
    # with open(file_name, 'w') as f:
    #     copyfileobj(gen_imports(), f)
    #     copyfileobj(gen_protocols(), f)
    #     copyfileobj(gen_main(num_nodes), f)
    #     copyfileobj(file_closing, f)
