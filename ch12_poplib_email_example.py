"""
ch12_poplib_email_example.py

Program which fetches and prints out all your
email waiting at a POP3 server.
"""
import poplib, email

HOST   = "localhost"
PORT   = 110
USER   = "username"
PASSWD = "password"

M = poplib.POP3(HOST, PORT)
M.user(USER)
M.pass_(PASSWD)
numMessages = len(M.list()[1])
for i in range(numMessages):
    msg_txt = "\n".join(M.retr(i+1)[1])
    msg     = email.message_from_string(msg_txt)
    print msg['Subject']

M.quit()
