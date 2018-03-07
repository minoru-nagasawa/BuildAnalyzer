#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import datetime as dt
import pprint 
from sets import Set
import math
import copy

class FileInfo:
  def __init__(self, a_filename):
    self.Name = a_filename
    self.__isRead   = False
    self.__isWrite  = False
    self.__isDelete = False
    self.__isCreate = False
    self.__isStat   = False
    self.__close_on_exec = False
  def SetReadOn(self):
    self.__isRead = True
  def SetReadOn(self):
    self.__isRead = True
  def SetWriteOn(self):
    self.__isWrite = True
  def SetDeleteOn(self):
    self.__isDelete = True
  def SetCreateOn(self):
    self.__isCreate = True
  def SetStatOn(self):
    self.__isStat = True
  def SetCloseOnExecOn(self):
    self.__close_on_exec = True
  def IsRead(self):
    return self.__isRead
  def IsWrite(self):
    return self.__isWrite
  def IsDelete(self):
    return self.__isDelete
  def IsCreate(self):
    return self.__isCreate
  def IsStat(self):
    return self.__isStat
  def IsCloseOnExec(self):
    return self.__close_on_exec

class ProcessInfo:
  __id = 1

  def __init__(self, a_processId, a_currentDir, a_baseFiles, a_startDateTime):
    self.Id  = ProcessInfo.__id
    ProcessInfo.__id = ProcessInfo.__id + 1
    self.Pid = a_processId
    self.Dir = a_currentDir
    self.StartDateTime = a_startDateTime
    self.EndDateTime   = a_startDateTime
    self.ProcessName   = ""
    self.Parameter     = ""
    self.ChildProcess  = []
    self.CompletedFiles = {}
    self.Files = {}
    self.Files[0] = FileInfo("\"stdin\"")
    self.Files[1] = FileInfo("\"stdout\"")
    self.Files[2] = FileInfo("\"stderr\"")
    # sys.stderr.write("New Process:\n")
    for descriptor, fileInfo in a_baseFiles.iteritems():
      # sys.stderr.write("    " + str(descriptor) + " " + fileInfo.Name + ":" +  str(fileInfo.IsCloseOnExec()) + "\n")
      self.Files[descriptor] = copy.deepcopy(fileInfo)

class ProcessInfoCollection:
  def __init__(self, a_startDir):
    self.__dict = {}
    self.__startDir = a_startDir
    
  def AddProcess(self, a_basePid, a_createPid, a_startDateTime):
    #sys.stderr.write("AddProcess:" + str(a_basePid) + "->" + str(a_createPid) + "\n")
    if a_basePid == -1:
      info = ProcessInfo(a_createPid, self.__startDir, {}, a_startDateTime)
    else:
      info = ProcessInfo(a_createPid, self.GetCurrentDir(a_basePid), self.__dict[a_basePid].Files, a_startDateTime)
      self.__dict[a_basePid].ChildProcess.append(info)
    self.__dict[a_createPid] = info

  def CloseProcess(self, a_processId):
    #sys.stderr.write("CloseProcess:" + str(a_processId) + "\n")
    return self.__dict.pop(a_processId)
  
  def AddOpenFile(self, a_processId, a_descriptor, a_filename):
    #sys.stderr.write("AddOpenFile:" + str(a_processId) + ":" + str(a_descriptor) + " " + a_filename + "\n")
    if a_filename[0:3] == "\"./":
      filename = "\"" + self.__dict[a_processId].Dir + a_filename[2:]
    elif a_filename[1] != "/":
      filename = "\"" + self.__dict[a_processId].Dir + "/" + a_filename[1:]
    else:
      filename = a_filename
    self.__dict[a_processId].Files[a_descriptor] = FileInfo(filename)

  def AddPipe(self, a_processId, a_inputDescriptor, a_outputDescriptor):
    #sys.stderr.write("AddPipe:" + str(a_processId) + ":" + str(a_inputDescriptor) + "->" + str(a_outputDescriptor) + "\n")
    self.__dict[a_processId].Files[a_inputDescriptor]  = FileInfo("\"pipe\"")
    self.__dict[a_processId].Files[a_outputDescriptor] = FileInfo("\"pipe\"")
  
  def GetOpenFile(self, a_processId, a_descriptor):
    return self.__dict[a_processId].Files[a_descriptor]
  
  def DupOpenFile(self, a_processId, a_descriptorFrom, a_descriptorTo):
    #sys.stderr.write("DupOpenFile:" + str(a_processId) + ":" + str(a_descriptorFrom) + "->" + str(a_descriptorTo) + "\n")
    if a_descriptorTo in self.__dict[a_processId].Files:
      self.CloseFile(a_processId, a_descriptorTo)

    self.__dict[a_processId].Files[a_descriptorTo] = copy.deepcopy(self.__dict[a_processId].Files[a_descriptorFrom])

  def CloseFile(self, a_processId, a_descriptor):
    #sys.stderr.write("CloseFile:" + str(a_processId) + ":" + str(a_descriptor) + "\n")
    tmp = self.__dict[a_processId].Files[a_descriptor]
    if  tmp.Name != "stdin"  \
    and tmp.Name != "stdout" \
    and tmp.Name != "stderr" \
    and tmp.Name != "pipe":
      del self.__dict[a_processId].Files[a_descriptor]
      if tmp.Name in self.__dict[a_processId].CompletedFiles:
        d = self.__dict[a_processId].CompletedFiles[tmp.Name]
        if d.IsRead():
          d.SetReadOn()
        if d.IsWrite():
          d.SetWriteOn()
        if d.IsDelete():
          d.SetDeleteOn()
        if d.IsCreate():
          d.SetCreateOn()
        if d.IsStat():
          d.SetStatOn()
        self.__dict[a_processId].CompletedFiles[tmp.Name] = d
      else:
        self.__dict[a_processId].CompletedFiles[tmp.Name] = tmp

  def ChangeDir(self, a_processId, a_directory):
    self.__dict[a_processId].Dir = a_directory
  
  def GetCurrentDir(self, a_processId):
    return self.__dict[a_processId].Dir
  
  def SetEndDateTime(self, a_processId, a_endDateTime):
    self.__dict[a_processId].EndDateTime = a_endDateTime
  
  def SetProcessInfo(self, a_processId, a_processName, a_parameter):
    self.__dict[a_processId].ProcessName = a_processName
    self.__dict[a_processId].Parameter   = a_parameter
  
  def GetProcessInfo(self, a_processId):
    if a_processId in self.__dict:
      return self.__dict[a_processId]
    else:
      return None

  def CloseFilesCloseOnExec(self, a_processId):
    files = self.__dict[a_processId].Files
    closeFiles = []
    for descriptor, fileInfo in files.iteritems():
      if fileInfo.IsCloseOnExec():
        closeFiles.append(descriptor)
    for descriptor in closeFiles:
        self.CloseFile(a_processId, descriptor)

class Parser:
  def __init__(self, a_startDir):
    # pid   hour min sec ms     syscall       ---arg---                ret us
    # 23006 18:59:27.331042 open("/etc/init.d/xinetd", O_RDONLY) = 0 <0.000007>
    #
    # Caution : _exit and exit_group do not have Time(<0.000007>)
    # 3713  03:28:47.965553 exit_group(0)     = ?
    self.reLine = re.compile(r"^(?P<pid>[0-9]+)\s+(?P<hour>[0-9][0-9]):(?P<min>[0-9][0-9]):(?P<sec>[0-9][0-9])\.(?P<ms>[0-9]+) ((?P<stopped>--- .*)|((?P<unfinished>.*)<unfinished \.\.\.>)|(<\.\.\. .* resumed>(?P<resumed>.*))|((?P<syscall>[^\(]+)\((?P<arg>.*)\)\s+=\s+(?P<ret>[^\s]+).*( <(?P<us>[0-9]+\.[0-9]+)>)?))")
    
    # 8029  18:59:27.331042 wait4(-1,  <unfinished ...>
    # 8029  18:59:28.331042 <... wait4 resumed> [{WIFEXITED(s) && WEXITSTATUS(s) == 0}], 0, NULL) = 8030 <0.086457>
    self.unfinish = {}
    
    self.m_processCollection = ProcessInfoCollection(a_startDir)
    self.m_completedProcessList = []
  
  def GetParseResult(self):
    return self.m_completedProcessList

  def Parse(self, a_line):
    m = self.reLine.match(a_line)
    #if m:
    #  if m.group("syscall"):
    #    sys.stderr.write(m.group("syscall") + ":" + a_line)
    #  else:
    #    sys.stderr.write("Partial match:" + a_line)
    #else:
    #  sys.stderr.write("No match: " + a_line)

    if m:
      if m.group("unfinished"):
        self.unfinish[int(m.group("pid"))] = "%s %s:%s:%s.%s %s" % (m.group("pid"), m.group("hour"), m.group("min"), m.group("sec"), m.group("ms"), m.group("unfinished"))
        # sys.stderr.write("unfinished:" + a_line+"\n")
      elif m.group("resumed"):
        line = self.unfinish[int(m.group("pid"))] + m.group("resumed")
        m2 = self.reLine.match(line)
        # sys.stderr.write("resumed:" + line+"\n")
        self.__dispatch(m2, self.m_processCollection)
      else:
        self.__dispatch(m, self.m_processCollection)
        
  def __dispatch(self, a_match, a_collection):
    syscall = a_match.group("syscall")
    # 989   04:51:17.911406 clone(child_stack=0, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x2b967bdc1fe0) = 990 <0.000050>
    # 18912 05:40:35.694551 vfork()           = 18913 <0.000157>
    if syscall == "clone" or syscall == "vfork":
      a_collection.AddProcess(int(a_match.group("pid")), int(a_match.group("ret")), Parser.__getDateTime(a_match))
      
    # 989   04:51:17.691293 execve("./test_main.sh", ["./test_main.sh"], [/* 22 vars */]) = 0 <0.000066>
    elif syscall == "execve":
      pid  = int(a_match.group("pid"))
      info = a_collection.GetProcessInfo(pid)
      if info is None:
        a_collection.AddProcess(-1, pid, Parser.__getDateTime(a_match))
      
      tmp = Parser.__parseArgument(a_match.group("arg"))
      a_collection.SetProcessInfo(pid, tmp[0], tmp[1])
      a_collection.CloseFilesCloseOnExec(pid)
    
    # 990   04:51:17.952055 open("/etc/ld.so.cache", O_RDONLY) = 3 <0.000007>
    elif syscall == "open":
      ret = int(a_match.group("ret"))
      if ret >= 0:
        pid = int(a_match.group("pid"))
        tmp = Parser.__parseArgument(a_match.group("arg"))
        filename = tmp[0]
        a_collection.AddOpenFile(pid, ret, filename)

        arg = tmp[1]
        if "O_CREAT" in arg:
          a_collection.GetOpenFile(pid, ret).SetCreateOn()

      
    # 23148 11:53:59.198558 read(3, "\177ELF\2\1\1\0\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0\360\332\201\221?\0\0\0"..., 832) = 832
    elif syscall == "read":
      pid = int(a_match.group("pid"))
      descriptor = int(Parser.__parseArgument(a_match.group("arg"))[0])
      a_collection.GetOpenFile(pid, descriptor).SetReadOn()
      
    # 23149 11:53:59.224510 write(1, " === start sub thread (method) ="..., 36) = 36
    elif syscall == "write":
      pid = int(a_match.group("pid"))
      descriptor = int(Parser.__parseArgument(a_match.group("arg"))[0])
      a_collection.GetOpenFile(pid, descriptor).SetWriteOn()

    # 574  11:53:59.224510  stat("/home/xxx", {st_mode=S_IFDIR|0775, st_size=4096, ...}) = 0 <0.000378>
    # elif syscall == "stat":
    #   ret = int(a_match.group("ret"))
    #   if ret >= 0:
    #     pid = int(a_match.group("pid"))
    #     filename = Parser.__parseArgument(a_match.group("arg"))[0]
    #     a_collection.AddOpenFile(pid, -1, filename)
    #     a_collection.GetOpenFile(pid, -1).SetStatOn()
    #     a_collection.CloseFile(pid, -1)

    # 573  11:53:59.224510 close(3)                          = 0 <0.000355>
    elif syscall == "close":
      ret = int(a_match.group("ret"))
      if ret >= 0:
        pid = int(a_match.group("pid"))
        descriptor = int(Parser.__parseArgument(a_match.group("arg"))[0])
        a_collection.CloseFile(pid, descriptor)

    # 3714  03:28:48.254705 rename("/tmp/from.dat", "/tmp/to.dat") = 0 <0.002298>
    elif syscall == "rename":
      pid = int(a_match.group("pid"))
      filename = Parser.__parseArgument(a_match.group("arg"))
      fromFile = filename[0]
      a_collection.AddOpenFile(pid, -1, fromFile)
      a_collection.GetOpenFile(pid, -1).SetDeleteOn()
      a_collection.CloseFile(pid, -1)

      toFile = filename[0]
      a_collection.AddOpenFile(pid, -1, toFile)
      a_collection.GetOpenFile(pid, -1).SetCreateOn()
      a_collection.CloseFile(pid, -1)

    # 11412 04:08:30.836925 pipe([3, 4])      = 0 <0.000008>
    elif syscall == "pipe":
      pid = int(a_match.group("pid"))
      arg = Parser.__parseArgument(a_match.group("arg"))[0] # "[3, 4]""
      arg = arg[1: -1] # "3, 4"
      comma = arg.find(",")
      inputDescriptor  = int(arg[0: comma])
      outputDescriptor = int(arg[comma + 1 :])
      a_collection.AddPipe(pid, inputDescriptor, outputDescriptor)
    
    # 3744  03:37:33.936350 chdir("/tmp")     = 0 <0.000365>
    elif syscall == "chdir":
      pid = int(a_match.group("pid"))
      dirname = Parser.__parseArgument(a_match.group("arg"))[0]
      a_collection.ChangeDir(pid, dirname[1:-1]) # [1:-1] is remove double quotation
    
    # 573   11:53:59.198558 dup2(3, 255)                      = 255
    elif syscall == "dup2":
      pid = int(a_match.group("pid"))
      args = Parser.__parseArgument(a_match.group("arg"))
      a_collection.DupOpenFile(pid, int(args[0]), int(args[1]))

    # 19908 07:01:20.612911 fcntl(1, F_DUPFD, 10) = 10 <0.000003>
    # 19908 07:01:20.612939 fcntl(10, F_SETFD, FD_CLOEXEC) = 0 <0.000003>
    # 20354 09:31:44.226753 fcntl(10, F_GETFD) = 0x1 (flags FD_CLOEXEC) <0.000002>
    elif syscall == "fcntl":
      ret = int(a_match.group("ret"), 0) # As the result may be a hexadecimal number (0x##), specify 0 for the second argument of int.
      if ret >= 0:
        pid  = int(a_match.group("pid"))
        args = Parser.__parseArgument(a_match.group("arg"))
        desc = int(args[0])
        cmd  = args[1]
        if cmd == "F_DUPFD":
          a_collection.DupOpenFile(pid, desc, ret)
        if cmd == "F_DUPFD_CLOEXEC":
          a_collection.DupOpenFile(pid, desc, ret)
          a_collection.GetOpenFile(pid, ret).SetCloseOnExecOn()
        if cmd == "F_SETFD" and args[2] == "FD_CLOEXEC":
          a_collection.GetOpenFile(pid, desc).SetCloseOnExecOn()

    # 3715  03:28:48.355670 unlink("/tmp/to.dat") = 0 <0.000838>
    elif syscall == "unlink":
      ret = int(a_match.group("ret"))
      if ret >= 0:
        pid = int(a_match.group("pid"))
        filename = Parser.__parseArgument(a_match.group("arg"))[0]
        a_collection.AddOpenFile(pid, -1, filename)
        a_collection.GetOpenFile(pid, -1).SetDeleteOn()
        a_collection.CloseFile(pid, -1)

    # 3713  03:28:47.965553 exit_group(0)     = ?
    # 23149 11:54:02.235461 _exit(0)          = ?
    elif syscall == "_exit" or syscall == "exit_group":
      tmp = a_collection.CloseProcess(int(a_match.group("pid")))
      if tmp.ProcessName == "":
         tmp.ProcessName = "\"thread\""

      tmp.EndDateTime = Parser.__getDateTime(a_match)
      self.m_completedProcessList.append(tmp)
      
  @staticmethod
  def __getDateTime(a_match):
    today = dt.date.today()
    return dt.datetime(today.year, today.month, today.day, int(a_match.group("hour")), int(a_match.group("min")), int(a_match.group("sec")), int(a_match.group("ms")))
  
  # arg = open("/dev/tty", O_RDWR|O_NONBLOCK) => ["\"/dev/tty\", "O_RDWR|O_NONBLOCK"]
  #            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  @staticmethod
  def __parseArgument(a_arg):
    i = 0
    start = 0
    retVal = []
    while i < len(a_arg):
      # Double quoted text
      if a_arg[i] == "\"":
        while i < len(a_arg):
          if a_arg[i] == "\"":
            break
          if a__arg[i] == "\\" and a_arg[i + 1] == "\"":
            i += 1
          i += 1
      # Parenthesized argument
      # 989   04:51:17.747045 fstat(3, {st_mode=S_IFREG|0755, st_size=1726296, ...}) = 0 <0.000406>
      elif a_arg[i] == "{":
        while i < len(a_arg):
          if a_arg[i] == "}":
            break
          i += 1
          
      # Parenthesized argument
      # 989   04:51:17.691293 execve("./test_main.sh", ["./test_main.sh"], [/* 22 vars */]) = 0 <0.000066>
      elif a_arg[i] == "[":
        while i < len(a_arg):
          if a_arg[i] == "]":
            break
          i += 1
          
      elif a_arg[i] == ",":
        retVal.append(a_arg[start : i])
        while i + 1 < len(a_arg) and a_arg[i + 1] == " ":
          i += 1
        start = i + 1

      i += 1
    
    # last argument
    retVal.append(a_arg[start : ])
    
    return retVal

class DependFormatter:
  @staticmethod
  def Output(a_fileName, a_collection):
    f = open(a_fileName, "w")
    try:
      # Output process nodes
      plen = len(a_collection)
      pwidth = int(math.log10(plen)) + 1
      f.write("Create\n")
      for p in a_collection:
        diff = p.EndDateTime - p.StartDateTime
        diff_seconds = diff.days * 3600 * 24 + diff.seconds + diff.microseconds / 1000000.0
        parameter = p.Parameter.replace("\"", "'")
        f.write("    (pid%0*d:Process{id:%0*d, dir:\"%s\", time:%f, name:%s, param:\"%s\"}),\n" % (pwidth, p.Id, pwidth, p.Id, p.Dir, diff_seconds, p.ProcessName, parameter))
      f.write("\n")

      # Output process relations
      for p in a_collection:
        for c in p.ChildProcess:
          f.write("    (pid%0*d)-[:CALL]->(pid%0*d),\n" % (pwidth, p.Id, pwidth, c.Id))
      f.write("\n")

      # Create unique file set
      uniqueFile = {}
      fid = 1
      for p in a_collection:
        for file in p.CompletedFiles.keys():
          if not file in uniqueFile:
            uniqueFile[file] = fid
            fid += 1

      # Output file nodes
      flen = len(uniqueFile)
      fwidth = int(math.log10(flen)) + 1
      for file, fid in uniqueFile.iteritems():
        f.write("    (fid%0*d:File{name:%s}),\n" % (fwidth, fid, file))
      f.write("\n")

      # Create relations of process to file
      for p in a_collection:
        for file in p.CompletedFiles.keys():
          fid = uniqueFile[file]
          tmp = p.CompletedFiles[file]
          read = str(tmp.IsRead())
          write = str(tmp.IsWrite())
          delete = str(tmp.IsDelete())
          create = str(tmp.IsCreate())
          f.write("    (pid%0*d)-[:ACCESS{read:%-6s, write:%-6s, delete:%-6s, create:%-6s}]->(fid%0*d),\n" % (pwidth, p.Id, read, write, delete, create, fwidth, fid))

      # To end with a semicolon, make :Dummy and delete it
      f.write("\n")
      f.write("    (:DUMMY);\n")
      f.write("MATCH (d:DUMMY) DELETE d;\n")

    finally:
      f.close()

    # for p in a_collection:
    #   sys.stderr.write(str(p.Id) + " " + p.ProcessName + ":" + str(p.StartDateTime) + " - " + str(p.EndDateTime) + "\n")
    #   sys.stderr.write("Call Process:\n")
    #   for c in p.ChildProcess:
    #     sys.stderr.write("    [" + c.ProcessName + "]\n")
    #   sys.stderr.write("Access File:\n")
    #   for c in p.CompletedFiles.values():
    #     sys.stderr.write("    [" + c.Name + "]\n")

class TimeFormatter:
  @staticmethod
  def Output(a_collection):
    pass

def main():
  # analyze option
  skip = 0
  option = ""
  dir = ""
  prefix = ""
  debug = False
  for index, arg in enumerate(sys.argv):
    if skip > 0:
      skip -= 1
      if option == "--dir":
        dir = arg
      elif option == "--file-prefix":
        prefix = arg
    else:
      if arg == "--dir":
        option = arg
        skip = 1
      elif arg == "--file-prefix":
        option = arg
        skip = 1
      elif arg == "--debug":
        debug = True

  if dir == "" or prefix == "":
    sys.stderr.write("Usage: piped_build_analyze.py --dir root-dir --file-prefix file-prefix [--debug]\n")
    sys.stderr.write("       input dir is [" + dir + "]\n")
    sys.stderr.write("       input prefix is [" + prefix + "]\n")
    sys.exit()

  # execute
  parser = Parser(dir)
  if debug:
    f = open(prefix + ".debug.txt", "w")
    try:
      for line in sys.stdin:
        f.write(line)
        parser.Parse(line)
    finally:
      f.close()
  else:
    for line in sys.stdin:
      parser.Parse(line)
    
  DependFormatter.Output(prefix + ".cypher", parser.GetParseResult())

if __name__ == "__main__":
  main()

