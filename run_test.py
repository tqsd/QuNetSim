import glob
import os
import subprocess

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


if __name__=="__main__":
    files = [f for f in glob.glob("./tests/**/*.py")] + [f for f in glob.glob("./tests/*.py")]
    print(files)
    for f in files:
        path, filename = os.path.split(f)
        with cd(path):
            exitcode = os.system("python %s" % (filename))
            if exitcode != 0:
                assert False, "Testfile %s was not succesfull!" % f
