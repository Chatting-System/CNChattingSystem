from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO, emit
from flask_socketio import join_room, leave_room, close_room
import re


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

userinformation = {}
client_to_sock = {}
sock_to_client = {}
chat_private = {}
blocked_by = {} #keys: users, values: list of users that have blocked this user
blocked = {} #keys: users, values: list of users that this user has blocked
#room database
id_to_name = {} 
id_to_description = {}
id_to_type = {}
id_to_creator = {}
room_stored = {} #This dic contains room_id, room_name, description and password. This should not be sent back to the client
members_information = {}
number = 0 #This number acts as the id of room so it should be incremented

@socketio.on('connect')
def test_connect():
    print("One user connect")
    emit('connection', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    user = session.pop('username')
    print("CONNECTION UNESTABLISHED")
    sid = client_to_sock.pop(user)
    sock_to_client.pop(sid)
    rid = ''
    for key in members_information.keys():
        if user in members_information[key]:
            rid = str(key)
    
    if rid != '':
        name = id_to_name[rid]
        creator = room_stored[rid][3]
        if user != creator:
            #In this case, it means the exiting person is not the creator of the room
            leave_room(name)
            members_information[rid].remove(user)
            emit('join success', {'room': name, 'rid': rid, 'members': members_information[rid]}, room = name)
        else:
            #In this case, it means the exiting person is the creator of the room
            emit('exit success', {'data': 'exit success'}, room = name)
            close_room(name)
            id_to_name.pop(rid)
            id_to_description.pop(rid)
            id_to_type.pop(rid)
            id_to_creator.pop(rid)
            room_stored.pop(rid)
            members_information.pop(rid)
            emit('new room', {'existing_rooms_ids': list(id_to_name.keys()), 'existing_rooms_names': list(id_to_name.values()), 'existing_rooms_descriptions': list(id_to_description.values()), 'type': list(id_to_type.values()), 'creator': list(id_to_creator.values())}, broadcast=True)
    for user in client_to_sock.keys():
        emit('user change', {'blocked_users': blocked[user], 'connected_users': list(client_to_sock.keys())},
             room=client_to_sock[user])

@socketio.on('connection')
def connection_success(message):
    msg = session['username']
    print("CONNECTION ESTABLISHED")
    client_to_sock[msg] = request.sid
    sock_to_client[request.sid] = msg
    emit('connection success', msg)
    print(list(client_to_sock.keys()))
    #emit('user change', {'connected_users': list(client_to_sock.keys())}, broadcast=True)
    emit('new room', {'existing_rooms_ids': list(id_to_name.keys()), 'existing_rooms_names': list(id_to_name.values()), 'existing_rooms_descriptions': list(id_to_description.values()), 'type': list(id_to_type.values()), 'creator': list(id_to_creator.values())}, broadcast=True)
    for user in client_to_sock.keys():
        emit('user change', {'user': user, 'blocked_users': blocked[user], 'connected_users': list(client_to_sock.keys())}, room=client_to_sock[user])

@app.route("/", methods=['GET', 'POST'])
def intial():
    return redirect('/daymode')

@app.route('/<mode>', methods=['GET', 'POST'])
def start(mode):
    if request.method == 'GET':
        print("NEW CONNECTION")
        return render_template("login.html", mode=mode)
    else:
        username = request.form['username']
        password = request.form['password']

        recordedpassword = userinformation.get(username, 'NULL')
        if recordedpassword == 'NULL':
            return render_template('login.html', error='Unknown username!', mode=mode)
        elif recordedpassword != password:
            return render_template('login.html', error='Wrong password!', mode=mode)
        elif username in client_to_sock.keys():
            return render_template('login.html', error="This account has already logged in!", mode=mode)
        else:
            session['username'] = username
            return render_template('test.html', mode=mode)


@app.route('/register/<mode>', methods=['GET', 'POST'])
def toregister(mode):
    if request.method == 'GET':
        return render_template("register.html", mode=mode)
    else:
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        check = re.search(r"\W", username)
        if check != None:
            return render_template('register.html', error='Invalid Username!', mode=mode)

        find_existing_username = userinformation.get(username, 'NULL')
        if find_existing_username != 'NULL':
            return render_template('register.html', error='The username already exists!', mode=mode)
        elif confirm != password:
            return render_template('register.html', error='The passwords do not match!', mode=mode)
        else:
            userinformation[username] = password
            blocked_by[username] = []
            blocked[username] = []
            return redirect('/' + mode)
            #return render_template('register.html', success='Success!', mode=mode)

@socketio.on('my event')
def my_event(message):
    try:
        if chat_private[session.get('username')] in blocked_by[session.get('username')]:
            emit('message blocked', chat_private[session.get('username')])
        else:
            emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username'),
                                 "private": 1, "to": "you"},
                 room=client_to_sock[chat_private[session.get('username')]])
            emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username'),
                                 "private": 1, "to": chat_private[session.get('username')]},
                 room=request.sid)
    except KeyError:
        for user in sock_to_client.keys():
            if sock_to_client[user] in blocked_by[session.get('username')]:
                continue
            emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username'),
                                 "private": 0},
                 room=user)

@socketio.on('set partner')
def set_partner(msg):
    print("set partner request received")
    if msg == "all":
        try:
            del chat_private[session.get('username')]
            print("sending to everyone")
            emit('set partner success', msg)
        except KeyError:
            print("still sending to everyone")
    elif msg != session.get('username'):
        print(f"setting {msg} as partner")
        chat_private[session.get('username')] = msg
        emit('set partner success', msg)

@socketio.on('block')
def block(user):
    if user != session.get('username'):
        blocked_by[user].append(session.get('username'))
        blocked[session.get('username')].append(user)
        emit('block success', user)

@socketio.on('unblock')
def unblock(user):
    blocked_by[user].remove(session.get('username'))
    blocked[session.get('username')].remove(user)
    print(blocked_by[user])
    emit('unblock success', user)

######### CHAT ROOMS ##########

@socketio.on("create room")
def create_room(msg):
    global number
    name = msg.get('name')
    description = msg.get('description')
    password = msg.get('password', None)
    user = session['username']
    rid = str(number)
    id_to_name[rid] = name
    id_to_description[rid] = description
    if password == '':
        id_to_type[rid] = 'Public'
    else:
        id_to_type[rid] = 'Private'
    id_to_creator[rid] = user
    room_stored[rid] = [name, description, password, user]
    emit('new room', {'existing_rooms_ids': list(id_to_name.keys()), 'existing_rooms_names': list(id_to_name.values()), 'existing_rooms_descriptions': list(id_to_description.values()), 'type': list(id_to_type.values()), 'creator': list(id_to_creator.values())}, broadcast=True)
    join_room(name)
    members_information[rid] = [user]
    emit('join success', {'room': name, 'rid': rid, 'members': members_information[rid]}, room = name)
    number += 1

@socketio.on('enter room')
def enter_room(msg):
    rid = str(msg.get('rid'))
    name = id_to_name[rid]
    r_type = id_to_type[rid]
    user = session.get('username')
    if r_type == 'Public':
        join_room(name)
        members_information[rid].append(user)
        emit('join success', {'room': name, 'rid': rid, 'members': members_information[rid]}, room = name)
    else:
        emit('auth', {'rid': rid}, room=request.sid)

@socketio.on('please auth')
def auth(msg):
    authpassword = msg.get('authpassword')
    authrid = str(msg.get('authrid'))
    password = room_stored[authrid][2]
    if authpassword == password:
        user = session.get('username')
        rid = authrid
        name = id_to_name[rid]
        join_room(name)
        members_information[rid].append(user)
        emit('join success', {'room': name, 'rid': rid, 'members': members_information[rid]}, room = name)
    else:
        emit('auth fail', {'data': 'data'}, room=request.sid)

@socketio.on('exit room')
def exit_room(msg):
    user = session.get('username')
    rid = str(msg.get('rid'))
    name = id_to_name[rid]
    creator = room_stored[rid][3]
    if user != creator:
        #In this case, it means the exiting person is not the creator of the room
        leave_room(name)
        members_information[rid].remove(user)
        emit('join success', {'room': name, 'rid': rid, 'members': members_information[rid]}, room = name)
        emit('exit success', {'data': 'exit success'}, room = request.sid)
    else:
        #In this case, it means the exiting person is the creator of the room
        emit('exit success', {'data': 'exit success'}, room = name)
        close_room(name)
        id_to_name.pop(rid)
        id_to_description.pop(rid)
        id_to_type.pop(rid)
        id_to_creator.pop(rid)
        room_stored.pop(rid)
        members_information.pop(rid)
        emit('new room', {'existing_rooms_ids': list(id_to_name.keys()), 'existing_rooms_names': list(id_to_name.values()), 'existing_rooms_descriptions': list(id_to_description.values()), 'type': list(id_to_type.values()), 'creator': list(id_to_creator.values())}, broadcast=True)


@socketio.on('room chatting')
def room_emit(msg):
    data = msg.get('msg')
    rid = str(msg.get('room'))
    name = id_to_name[rid]
    time = msg.get('time')

    emit('room response', {'data': data, 'time': time, "name": session.get('username')}, room=name)

if __name__ == "__main__":
    socketio.run(app, debug=True)
