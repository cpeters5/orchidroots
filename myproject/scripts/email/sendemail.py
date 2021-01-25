#!/usr/local/bin/python3.5
# -*- coding: utf-8 -*-

import fbchat
from fbchat import Client
from fbchat.models import *
client = Client('cpeters5@yahoo.com', 'Not24get')
exit()
# from getpass import getpass
# username = str(input("Username: "))

no_of_friends = int(input("Number of friends: "))
for i in xrange(no_of_friends):
    name = str(input("Name: "))
    friends = client.getUsers(name)  # return a list of names
    friend = friends[0]
    msg = str(input("Message: "))
    sent = client.send(friend.uid, msg)
    if sent:
        print("Message sent successfully!")