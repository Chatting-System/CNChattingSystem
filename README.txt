Summary: This system is a simple chatting system, whose key functions are: allowing users to create chatting rooms and others can join in or leave the room. 
Besides this, we also add more functions in the system by refering to some functions of Zoom. 

configuration: 
main languages: Python, html, javascript
interpreter: Python 3.6
python inital modules: re
extra python modules: flask, flask_socketio
database: To make it simple enough, we implemented the database in the server part by using dictionaries

Operating list:
1. Before the system, we implemented a login/register function which allows users to:
login if the user has the account
register if the user don't have the account
Chech whether the input given by the users are valid. If not the system will give out error messages

2. After the users login, there is the whole chatting system which allows users to:
logout
view and send messages to the public
view and send messages to the other person (1 to 1 conversation)
view the list of online users
view the list of online chatting rooms and their basic information
create a chatting room
join in a chatting room
view and send meassages in a chatting room
leave a chatting room

File lists:
|---README.txt
|---HOWTO.txt
|---makefile
|---.idea
|   |---inspectionProfiles
|   |   |---Project_Default.xml
|   |   |---profiles_settings.xml
|   |---.gitignore
|   |---aws.xml
|   |---computerNetworking.iml
|   |---misc.xml
|   |---modules.xml
|   |---vcs.xml
|---templates
|   |---login.html
|   |---register.html
|   |---test.html
|---.gitignore
|---server.py
