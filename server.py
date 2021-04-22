from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, send
from flask_socketio import join_room, leave_room, close_room
import uuid
import re


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
userinformation = {}
client_to_sock = {}
sock_to_client = {}
chat_private = {}
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
    print("CONNECTION UNESTBLISHED")
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
    emit("user change", {'connected_users': list(client_to_sock.keys())}, broadcast=True)

@socketio.on('connection')
def connection_success(message):
    msg = session['username']
    print("CONNECTION ESTABLISHED")
    client_to_sock[msg] = request.sid
    sock_to_client[request.sid] = msg
    emit('connection success', msg)
    print(list(client_to_sock.keys()))
    emit("user change", {'connected_users': list(client_to_sock.keys())}, broadcast=True)
    emit('new room', {'existing_rooms_ids': list(id_to_name.keys()), 'existing_rooms_names': list(id_to_name.values()), 'existing_rooms_descriptions': list(id_to_description.values()), 'type': list(id_to_type.values()), 'creator': list(id_to_creator.values())}, broadcast=True)

@app.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'GET':
        print("NEW CONNECTION")
        return render_template("login.html")
    else:
        username = request.form['username']
        password = request.form['password']

        recordedpassword = userinformation.get(username, 'NULL')
        if recordedpassword == 'NULL':
            return render_template('login.html', error='Unknown username!')
        elif recordedpassword != password:
            return render_template('login.html', error='Wrong password!')
        elif username in client_to_sock.keys():
            return render_template('login.html', error="This account has already logged in!")
        else:
            session['username'] = username
            return render_template('test.html')


@app.route('/register', methods=['GET', 'POST'])
def toregister():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        check = re.search(r"\W", username)
        if check != None:
            return render_template('register.html', error='Invalid Username!')

        find_existing_username = userinformation.get(username, 'NULL')
        if find_existing_username != 'NULL':
            return render_template('register.html', error='The username already exists!')
        elif confirm != password:
            return render_template('register.html', error='The passwords do not match!')
        else:
            userinformation[username] = password
            return redirect('/')
            #return render_template('register.html', success='Success!')

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





# @app.route('/create', methods=["POST"])
# def create_room():
#     room_name = request.form.get('room_name')
#     room_description = request.form.get('description')
#     room_password = request.form.get('room_password', '')
#     room_id = str(uuid.uuid1().int)
#     id_to_name[room_id] = room_name
#     id_to_description[room_id] = room_description
#     room_stored[room_id] = [room_name, room_description, room_password]
#     # print(room_name)
#     # print(room_description)
#     # print(room_password)
#     # print(room_password == '')
#     socketio.emit('new room', {'existing_rooms_ids': list(id_to_name.keys()), 'existing_rooms_names': list(id_to_name.values()), 'existing_rooms_descriptions': list(id_to_description.values())}, broadcast=True)
#     return redirect('/chatroom/{}'.format(room_id))

# @app.route('/chatroom/<room_id>', methods=["POST", "GET"])
# def room_in(room_id):
#     username = session['username']
#     room_name = room_stored[room_id][0]
#     join_room(room_name)
#     return render_template("room.html", room_name = room_name, username=username)

@socketio.on('room chatting')
def room_emit(msg):
    data = msg.get('msg')
    rid = str(msg.get('room'))
    name = id_to_name[rid]
    time = msg.get('time')

    emit('room response', {'data': data, 'time': time, "name": session.get('username')}, room=name)

@socketio.on('my event')
def my_event(message):
    try:
        emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username'),
                             "private": 1, "to": "you"},
             room=client_to_sock[chat_private[session.get('username')]])
        emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username'),
                             "private": 1, "to": chat_private[session.get('username')]},
             room=request.sid)
    except KeyError:
        emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username'),
                             "private": 0}, broadcast=True)

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


# @app.route('/ajax', methods = ['POST'])
# def ajax_request():
#     username = request.form['username']
#     time = request.form['time']
#     return jsonify(username=username, time=time)
    
    
if __name__ == "__main__":
    socketio.run(app, debug=True)
