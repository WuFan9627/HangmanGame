import socket
import sys
import threading
import random
import traceback
from time import sleep
HOST = '0.0.0.0'
PORT = 8888 
users = {}
words = set()
games = {}
conns = {}
logins = {}#--id

def difficultyName(d):
    d = int(d)
    if d == 1:
        return 'Easy'
    elif d == 2:
        return 'Medium'
    else:
        return 'Hard'

def update(game):
    sleep(0.1)
    #game end: print ' send end' and then pop user
    if game['end']:
        for user in game['users']:
            if user in logins:
                logins[user].send('end')
        if game['id'] in games:
            games.pop(game['id'])
        return
    #game not end: show the correct guess letter and '_'
    resp = '\n'
    for ch in game['word']:
        if ch in game['rights']:
            resp += ch
        else:
            resp += '_'
    for i in range(len(game['wrongs'])):
        if i % len(game['word']) == 0:
            resp += '\n'
        resp += game['wrongs'][i]
    resp += '\n'
    for i in  range(len(game['users'])):
        resp += game['users'][i] + '\t'
        resp += str(users[game['users'][i]]['score']) 
        if i == game['current']:
            resp += ' *'
        resp += '\n'
    for user in game['users']:
        if user in logins:
            logins[user].send(resp)
    
def isWin(game):
    for i in range(len(game['word'])):
        if game['word'][i] not in game['rights']:
            return False
    return True

def isLost(game):
    if game['difficulty'] == '1':
        if len(game['wrongs']) >= len(game['word']) * 3:
            return True
    elif game['difficulty'] == '2':
        if len(game['wrongs']) >= len(game['word']) * 2:
            return True
    elif game['difficulty'] == '3':
        if len(game['wrongs']) >= len(game['word']):
            return True
    return False               
                    
#sub threading
def process(s):
    while True:
        if s not in conns:
            conns[s] = None #if the user not login then make it none
            
        data = s.recv(1024)
        if data == 'exit' or not data:
            conns.pop(s)
            return
        
        ss = data.split()
        key = ss[0]
        if key == 'register':
            if ss[1] in users:
                # duplicate username
                s.send('err')
            else:
                users[ss[1]] = {'name':ss[1], 'password':ss[2], 'score':0, 'game':None};  
                s.send('ok')
            
        elif key == 'login':
            if ss[1] not in users or ss[2] != users[ss[1]]['password']:
                s.send('err')
            else:
                conns[s] = ss[1]
                logins[ss[1]] = s
                s.send('ok')
        elif key == 'hall':
            res = []
            for user in users:
                res.append((users[user]['score'], user))
            res = sorted(res, reverse=True)
            resp = ''
            for user in res:
                resp += user[1] + '\t' + str(user[0]) + '\n'
            s.send(resp)
                
        elif conns[s] == None:
            s.send('err not login')
            return
            
        elif key == 'newgame':
            id = 1
            while id in games:
                id += 1
            games[id] = {'id':id, 'users':[], 'current':0, 'difficulty':ss[1], 'word':list(words)[random.randint(0, len(words)) - 1], 'wrongs':[], 'rights':[]}
            s.send(str(id))
            
        elif key == 'games':
            resp = '0. Exit\n'
            for key in games:
                game = games[key]
                resp += str(game['id']) + '. ' + difficultyName(game['difficulty']) + '\n'
            s.send(resp)
        elif key == 'join':
            id = int(ss[1])
            user = conns[s]
            if id not in games:
                s.send('err')
            else:
                game = games[id]
                game['users'].append(user)
                update(game)

# start playing
                while True:
                    try:
                        word = s.recv(1024)
#current user guess one letter when it is his turn then move to next user
                        if len(word) == 1 and game['users'][game['current']] == user:
                            if word in game['rights']:
                                game['current'] += 1
                                game['current'] %= len(game['users'])
                            elif word in game['wrongs']:
                                game['current'] += 1
                                game['current'] %= len(game['users'])
                            elif word in game['word']:
                                game['rights'].append(word)
                                users[user]['score'] += 1
                                if isWin(game):
                                    users[user]['score'] += len(game['word']) #add the score for this correct word
                                    update(game)
                                    game['end'] = True
                                    update(game)
                                    break
                            else:
                                game['wrongs'].append(word)
                                game['current'] += 1
                                game['current'] %= len(game['users'])
                                
                        else:
                            if word == game['word']:# guess when not his turn
                                del game['rights'][:]
                                for i in range(len(game['word'])):
                                    game['rights'].append(game['word'][i])
                                users[user]['score'] += len(game['word'])
                                update(game)
                                game['end'] = True
                                update(game)
                                break
                            else:
                                game['users'].remove(user) #remove when it is not his turn and guess wrong
                                s.send('end')
                                update(game)
                                break
                        if isLost(game):
                            game['end'] = True
                        update(game)
                    except Exception, ex:
                        print 'err'
                        print ex
                        traceback.print_exc()
                        logins.pop(conns[s])
                        conns[s] = None
                        s.close()
                        return

            
        elif key == 'logout':
            logins.pop(conns[s])
            conns[s] = None
    s.close()
        
        
#waiting for tcp connection
def tcpserver(s):
    while True:
        sock, addr = s.accept()
        t = threading.Thread(target=process, args=([sock]))
        t.start()
    s.close()


try :
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error, msg : 
    print 'Socket error: ' + str(msg[0]) + '   ' + msg[1]
    sys.exit()


# Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error , msg:
    print 'Bind error: ' + str(msg[0]) + '   ' + msg[1]
    sys.exit()

s.listen(5)
t = threading.Thread(target=tcpserver, args=([s]))
t.setDaemon(True)
t.start()

words.add('hangman')

#main threading
while True:

    print '\n1. Current list of the users'
    print '2. Current list of the words'
    print '3. Add new word to the list of words'
    print 'selection: '
    option = input()
    if option == 1:
        for user in users:
            print user
        print
    elif option == 2:
        for word in words:
            print word
        print
    elif option == 3:
        word = raw_input('new word: ')
        words.add(word)
    

            
