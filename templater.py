from io import StringIO
from shutil import copyfileobj
from templater_utils import gen_protocols
from templater_utils import gen_import_statements
from templater_utils import gen_main
from templater_utils import prompt_valid_num
from templater_utils import prompt_valid_filename
from templater_utils import prompt_host_names
from templater_utils import prompt_backend
from pathvalidate import ValidationError, validate_filename


if __name__ == '__main__':
    # file_name = prompt_valid_filename()
    # num_nodes = prompt_valid_num()
    # host_names = prompt_host_names(num_nodes)
    file_name = 'ex.py'
    back_end = prompt_backend()
    print(back_end)
    # file_closing = StringIO()
    # file_closing.write("if __name__ == '__main__':\n")
    # file_closing.write("   main()\n")
    # file_closing.seek(0)
    with open(file_name, 'w') as f:
        copyfileobj(gen_import_statements(back_end), f)
    #     copyfileobj(gen_protocols(), f)
    #     copyfileobj(gen_main(host_names), f)
    #     copyfileobj(file_closing, f)
