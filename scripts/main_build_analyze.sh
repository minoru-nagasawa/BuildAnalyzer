#!/bin/sh

if [ $# -le 1 ]; then
  echo usage: main_build_analyze.sh file_prefix [command [arg ...]]
  exit 1
fi

strace -s 1024 -tt -T -o "|./piped_build_analyze.py `pwd` $1" -f -e clone,execve,open,read,write,stat,close,rename,chdir,dup2,unlink,_exit,exit_group ${@:2}


