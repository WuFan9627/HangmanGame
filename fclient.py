import socket
import sys
import threading

end = False
#waiting for keyboard
def guess(s):
    while not end:
        word = raw_input()
        if not end:
            s.send(word)


# create a new threading
def play(s, name, game):
    global end
    s.send('join ' + str(game))
    resp = s.recv(1024)
    if resp == 'err':
        return
    print resp
    
    end = False
    t = threading.Thread(target=guess, args=[s])
    t.start()

#main threading
    while True:
        resp = s.recv(1024)
        if len(resp) == 0:
            end = True
            break
        if resp == 'end':
            end = True
            print 'Game over \n Press enter to continue'#continue the loop in the guess
            t.join()
            break
        print resp
#start after login successfully
def enter(s, name):
    while True:
        print '\n1. Start New Game'
        print '2. Get list of the Games'
        print '3. Hall of Fame'
        print '4. Exit'
        
        option = input('option: ')
        if option == 1:
            print 'Choose the difficulty:'
            print '1. Easy'
            print '2. Medium'
            print '3. Hard'
            difficulty = input('select: ')
            s.send('newgame ' + str(difficulty))

            game = s.recv(1024)

            play(s, name, game)
            
        elif option == 2:
            s.send('games')
            print s.recv(1024)
            game = input('select: ')
            if game == 0:
                continue
            play(s, name, game)
            
        elif option == 3:
            s.send('hall')
            print s.recv(1024)
            
        elif option == 4:
            s.send('logout')
            return


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if len(sys.argv) < 3:
    print 'Usage:', sys.argv[0], 'host port'
    s.close()
    sys.exit(1)
    
try: 
    s.connect((sys.argv[1], int(sys.argv[2])))
except:
    print 'Connect', sys.argv[1], sys.argv[2], 'error'
    sys.exit(1)

while True:
    print '\n1. Login'
    print '2. Make New User'
    print '3. Hall of Fame'
    print '4. Exit'
    option = input('option: ')
    if option == 1:
        name = raw_input('What is Your User Name? ')
        password = raw_input('What is Your Password? ')
        s.send('login ' + name + ' ' + password)
        ret = s.recv(1024)
        if ret == 'err':
            continue
        enter(s, name)
        
    elif option == 2:
        name = raw_input('What is Your User Name? ')
        password = raw_input('What is Your Password? ')
        s.send('register ' + name + ' ' + password)
        ret = s.recv(1024)
        if ret == 'err':
            print 'duplicate user name'
    elif option == 3:
        s.send('hall')
        print s.recv(1024)
    elif option == 4:
        s.close()
        sys.exit(0)

