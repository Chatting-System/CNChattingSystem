from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
userinformation = {}
client_to_sock = {}
sock_to_client = {}
chat_private = {}

@socketio.on('connect')
def test_connect():
    print("One user connect")
    emit('connection', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    username = session.pop('username')
    print("CONNECTION UNESTBLISHED")
    sid = sid = client_to_sock.pop(username)
    sock_to_client.pop(sid)
    print("{} user disconnect.".format(username))
    print(list(client_to_sock.keys()))
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


@app.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'GET':
        if session.get('username') != None:
            session.pop('username')
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

        find_existing_username = userinformation.get(username, 'NULL')
        if find_existing_username != 'NULL':
            return render_template('register.html', error='The username already exists!')
        elif confirm != password:
            return render_template('register.html', error='Your password and confirm are not the same!')
        else:
            userinformation[username] = password
            return render_template('register.html', success='Success!')



@socketio.on('my event')
def my_event(message):
    try:
        emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username')},
             room=client_to_sock[chat_private[session.get('username')]])
        emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username')},
             room=request.sid)
    except:
        emit('my response', {'data': message['data'], 'time': message['time'], "name": session.get('username')},
             broadcast=True)

@socketio.on('set partner')
def set_partner(msg):
    if msg == "all":
        del chat_private[session.get('username')]
        print("sending to everyone")
    else:
        chat_private[session.get('username')] = msg


# @app.route('/ajax', methods = ['POST'])
# def ajax_request():
#     username = request.form['username']
#     time = request.form['time']
#     return jsonify(username=username, time=time)
    
    
if __name__ == "__main__":
    socketio.run(app, debug=True)
