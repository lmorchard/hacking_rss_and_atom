"""
ch12_imaplib_example.py

Program which fetches and prints out all your
email waiting at a POP3 server.
"""
import imaplib

HOST   = "localhost"
PORT   = 143
USER   = "user"
PASSWD = "password"

M = imaplib.IMAP4(HOST, int(PORT))
M.login(USER, PASSWD)
M.select()
numMessages = M.search(None, "UNDELETED")[1][0].split()
for i in numMessages:
    print M.fetch(str(i), "RFC822")[1][0][1]
    break

M.close()
M.logout()

