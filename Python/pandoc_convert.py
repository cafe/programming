# 将本目录下一种格式用 Pandoc 转换成另一种格式(前提是 Pandoc 路径需要放在 PATH 变量下):

import sys
import os
from subprocess import call

def main(file_name):
    """
    convert file_name to .rst files
    """
    call("pandoc -s -S -t rst " + file_name + " -o " + os.path.splitext(file_name)[0] + ".rst")

if __name__ == '__main__':
    main(sys.argv[1])
