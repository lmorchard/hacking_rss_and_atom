"""
ch12_poplib_example.py

Program which fetches and prints out all your
email waiting at a POP3 server.
"""
import poplib

HOST   = "localhost"
PORT   = 110
USER   = "user"
PASSWD = "password"

M = poplib.POP3(HOST, PORT)
M.user(USER)
M.pass_(PASSWD)
numMessages = len(M.list()[1])
for i in range(numMessages):
    for j in M.retr(i+1)[1]:
        print j
    break

M.quit()
