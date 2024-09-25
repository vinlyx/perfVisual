#!/usr/bin/env python3

###### Import Modules
import sys
import os
import time
import datetime
import subprocess
import sqlite3

import psutil

###### Document Decription
"""  """

###### Version and Date
PROG_VERSION = '0.1.0'
PROG_DATE = '2024-09-24'

###### Usage
USAGE = """

     Version %s  by Vincent Li  %s

     Usage: %s <exe and parameter> >STDOUT
""" % (PROG_VERSION, PROG_DATE, os.path.basename(sys.argv[0]))

######## Global Variable


#######################################################################
############################  BEGIN Class  ############################
#######################################################################
class PerfVisual(object):
    """ docstring of PerfVisual """

    def __init__(self, interval: float=1.0):
        super().__init__()
        self.interval = interval
        self.db = None

    def exec(self, cmd: str, recordDB: str=None):
        self.db = self.initDB(recordDB)

        ## FIXME: since psutil can only record status of shell with
        ## shell=True, here use .split to convert cmdline into a list
        ## This method may cause unexpected issues.
        proc = subprocess.Popen(cmd.split(), shell=False)
        pm = ProcessMonitor(proc.pid)

        while proc.poll() is None:
            t0 = datetime.datetime.now()

            print(t0, pm.record())

            t1 = datetime.datetime.now()
            time.sleep(self.interval)
            # break

    def initDB(self, dbName: str=None):
        if not dbName:
            dbName = datetime.datetime.now().strftime("%Y%m%d_%H.%M.%S")


class ProcessMonitor(object):
    """ docstring of ProcessMonitor """

    def __init__(self, pid):
        super().__init__()
        self.proc = psutil.Process(pid)

    def record(self):
        p = self.proc # shortcut
        with p.oneshot():
            now = datetime.datetime.now()
            cpu_percent = p.cpu_percent()
            return (now, p.num_threads(), cpu_percent, p.memory_info().rss, p.io_counters())




##########################################################################
############################  BEGIN Function  ############################
##########################################################################


######################################################################
############################  BEGIN Main  ############################
######################################################################
#################################
##
##   Main function of program.
##
#################################
def main():

    ######################### Phrase parameters #########################
    import argparse
    ArgParser = argparse.ArgumentParser(usage=USAGE)
    ArgParser.add_argument("--version", action="version", version=PROG_VERSION)

    (params, args) = ArgParser.parse_known_args()

    if len(args) != 1:
        ArgParser.print_help()
        print("\n[ERROR]: The parameters number is not correct!", file=sys.stderr)
        sys.exit(1)
    else:
        (cmdLine,) = args # pylint: disable=unbalanced-tuple-unpacking

    ############################# Main Body #############################
    pv = PerfVisual(0.5)
    pv.exec(cmdLine)

    return 0

#################################
##
##   Start the main program.
##
#################################
if __name__ == '__main__':
    return_code = main()
    sys.exit(return_code)

################## God's in his heaven, All's right with the world. ##################