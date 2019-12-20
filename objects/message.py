

class Message(object):

    def __init__(self, sender, content, seq_num):
        self.sender = sender
        self.content = content
        self.seq_num = seq_num
