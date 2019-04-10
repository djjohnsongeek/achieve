import sqlite3


def sanitize(string): #lazy sanitization
    return ''.join(char for char in string if char.isalnum() or char == " ")

def insert_t1(clientName: str, clientID: int, clientNum: int, clientTeam: list, clients: list):
    
    """ adds T1 cliends to the given client's schedule """
