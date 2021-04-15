#Before building a virtual venv:
venv: 
	python3 -m venv venv

#After creating a virtual venv and activate it in the shell:
install: ./venv
	python3 -m pip install --upgrade pip
	pip install flask
	pip install flask-socketio
	pip install -U eventlet

run: install
	python3 server.py

#After finishing the operation of the system:
clean: 
	rm -rf venv




