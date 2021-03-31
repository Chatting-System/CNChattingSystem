from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@socketio.on('connect')
def test_connect():
    emit('connection', {'data': 'Connected'})

@socketio.on('connection')
def connection_success(message):
    emit('connection success', {'data': 'Hello User!'})

@app.route('/')
def index():
    return render_template("test.html")
        
@socketio.on('my event')
def my_event(message):
    emit('my response', {'data': message['data'], 'time': message['time']})

# @app.route('/ajax', methods = ['POST'])
# def ajax_request():
#     username = request.form['username']
#     time = request.form['time']
#     return jsonify(username=username, time=time)
    
    
if __name__ == "__main__":
    socketio.run(app, debug=True)
