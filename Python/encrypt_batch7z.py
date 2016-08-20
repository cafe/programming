# 调用7z命令行工具, 对目录下所有某种格式文件分别加密压缩成相应的单个文件 (用于个人私密资料上传网盘, 防止网盘对文件进行扫描).

import os
import sys
from subprocess import call

def main():
    """
    Archive each file to a 7z file with password protected
    """
    all_files = os.listdir()
    for file in all_files:
            filename = os.path.splitext(file)[0]
            if os.path.splitext(file)[1] == ".mkv":
                # call("pandoc -s -S " + file + " -o " + filename + ".org")
                    call("7z a -t7z " + filename + ".7z " + filename + ".mkv -mhe -mx9 -pPASSWORD") #-mhe to encrypt the file name, -mx9 ultra compression

if __name__ == '__main__':
    main()
