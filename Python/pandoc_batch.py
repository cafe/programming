# batch version of pandoc_convert.py

import os
import sys
from subprocess import call

def main():
"""
convert all .org files in current directory to .rst files
"""
all_files = os.listdir()
for file in all_files:
    filename = os.path.splitext(file)[0]
    if os.path.splitext(file)[1] == ".org":
        # call("pandoc -s -S " + file + " -o " + filename + ".org")
        call("pandoc -s -S -t rst " + file + " -o " + filename + ".rst")
if __name__ == '__main__':
main()
