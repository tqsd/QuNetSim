log_info = {
    "switch": False,
    "ack": False,
    "header_info": False,
    "epr_buffer": False,
    "data_buffer": False,
    "frame_content": True,
    "transmission_type": False,
    "data_transmission": False,
    "dense": False,
}


def log(key, message):
    if key in log_info and log_info[key] == True:
        print(message)
