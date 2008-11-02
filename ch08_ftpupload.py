#!/usr/bin/env python
"""
ch08_ftpupload.py

Given a remote filename and an optional local filename, upload a
file to an FTP server.
"""
import sys
from ftplib import FTP

FTP_HOST   = "localhost"
FTP_USER   = "youruser"
FTP_PASSWD = "yourpassword"
FTP_PATH   = "/www/www.example.com/docs"

def main():
    # Grab the remote filename as the final command line argument.
    remote_fn = sys.argv.pop()

    # If there's another argument, treat it as a filename to upload.
    if len(sys.argv) > 1:
        # Open the given filename, replace STDIN with it.
        local_fn  = sys.argv.pop()
        sys.stdin = open(local_fn, 'r')
    
    # Log into the FTP server, change directories, upload everything
    # waiting on STDIN to the given filename, then quit.
    ftp = FTP(FTP_HOST, FTP_USER, FTP_PASSWD)
    ftp.cwd(FTP_PATH)
    ftp.storbinary("STOR %s" % remote_fn, sys.stdin)
    ftp.quit()
    
if __name__ == '__main__': main()
