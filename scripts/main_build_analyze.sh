#!/bin/sh

if [ $# -le 1 ]; then
  echo Usage: main_build_analyze.sh file_prefix [command [arg ...]]
  exit 1
fi

THIS_DIR=$(dirname $(readlink -f $0))
strace -s 1024 -tt -T -o "|${THIS_DIR}/piped_build_analyze.py --dir `pwd` --file-prefix $1" -f -e clone,vfork,execve,open,read,write,stat,close,rename,pipe,chdir,dup2,fcntl,unlink,_exit,exit_group ${@:2}
# for debug
# strace -s 1024 -tt -T -o "|${THIS_DIR}/piped_build_analyze.py --dir `pwd` --file-prefix $1 --debug" -f ${@:2}
