from flask import Flask, request, jsonify, session
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

class User:

	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.passwordHash = str(generate_password_hash(password, "sha256"))
		self.valid = False
		self.debug = "test"
		self.token = None

	def signUp(self):
		conn = None

		try:
			conn = mysql.connector.connect(host='localhost', database='users', user='root', password= "rJ@mJ@r7")
			cursor = conn.cursor()
			query = "insert into users values (\'" + self.username + "\', \'" + self.passwordHash + "\', NULL)"
			cursor.execute(query)
			conn.commit()

		except Error as e:
			print(e)
		finally:
			cursor.close()
			conn.close()

	def updateID(self, token):
		self.token = str(token)
		conn = None
		data = {}
		try:
			conn = mysql.connector.connect(host= 'localhost', database= 'users', user='root', password = "rJ@mJ@r7")
			cursor = conn.cursor()
			query = "update users set publicID = \'" + self.token + "\' where username = \'" + self.username + "\'"
			cursor.execute(query)
			conn.commit()

		except Error as e:
			print(e)

		finally:
			self.debug = query
			conn.close()
			cursor.close()


	def isValid(self):
		query = "SELECT passwordHash FROM users WHERE username = \'" + self.username + "\' Limit 1"
		conn = None
		try:
			conn = mysql.connector.connect(host= 'localhost', database='users', user='root', password='rJ@mJ@r7')
			cursor = conn.cursor()
			cursor.execute(query)
			data = cursor.fetchone()
			if data != None and check_password_hash(str(data[0]), self.password):
				self.valid = True
			self.debug = self.passwordHash
		except Error as e:
			self.debug = str(e)

		finally:
			conn.close()
			cursor.close()

		return self.valid



def checkAuth():
	publicID = str(request.headers.get("Authentication"))
	query = "Select * from users where publicID = \'" + publicID + "\'"
	conn = None
	valid = False
	try:
		conn = mysql.connector.connect(host= 'localhost', database= 'users', user='root', password = "rJ@mJ@r7")
		cursor = conn.cursor()
		cursor.execute(query)
		row = cursor.fetchone()
		if row != None:
			valid = True

	except Error as e:
		print(e)

	finally:
		conn.close()
		cursor.close()
	return valid


# this function selects the most recent timestamp and temperature from a given table
def select_recent_data(datatype, table):
	query = "SELECT time_recieved, " + datatype + " FROM "+ table +" ORDER BY time_recieved DESC LIMIT 1"
	conn = None
	try:
		conn = mysql.connector.connect(host= 'localhost', database= 'greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor()
		cursor.execute(query)
		data = cursor.fetchone()
		timestamp = str(data[0])
		value = str(data[1])
	except Error as e:
		print(e)

	finally:
		conn.close()
		cursor.close()
		return [timestamp, value]

def select_all_statuses():
	query = "Select component, status, time_of_failure from status"
	conn = None
	data = {}
	try:
		conn = mysql.connector.connect(host= 'localhost', database= 'greenhouse_data', user='root', password = "rJ@mJ@r7")
		cursor = conn.cursor()
		cursor.execute(query)
		row = cursor.fetchone()
		while row is not None:
			data[row[0]] = [row[1], row[2]]
			row = cursor.fetchone()

	except Error as e:
		print(e)

	finally:
		conn.close()
		cursor.close()
		return data

def get_parameters():
	conn = None
	data = {}
	try:
		conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor()
		query = "SELECT * FROM parameters"
		cursor.execute(query)
		parameters = cursor.fetchone()

# fix the output dictionary keys to match the SQL keys !

		data["min_temp"] = str(parameters[0])
		data["max_temp"] = str(parameters[1])
		data["fert_water_conductivity"] = str(parameters[2])
		data["hydro_duration"] = str(parameters[3])
		data["hydro_freqency"] = str(parameters[4])
	except Error as e:
		print(e)

	finally:
		conn.close()
		cursor.close()
		return data

def update_parameters(columns, values):
	conn = None
	try:
		conn = mysql.connector.connect(host= 'localhost', database= 'greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor()

		for i in range(0, len(columns)):
			temp = ''
			temp = temp + columns[i]
			query = "UPDATE parameters SET " + temp + " = " + str(values[i])
			cursor.execute(query)

	except Error as e:
		print(e)

	finally:
		if conn != None:
			conn.commit()
			conn.close()
			cursor.close()
			return "Successful"
		else:
			return "Error"

def update_manual_controls(system, status):
	conn = None
	try:
		conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor()

		query = "UPDATE manual_controls SET" + system + " = " + str(status)
		cursor.execute(query)

	except Error as e:
		print(e)

	finally:
		conn.commit()
		conn.close()
		cursor.close()
		return "Updated"

def get_manual_controls():
	conn = None
	data = {}
	try:
		conn = mysql.connector.connect(host='localhost', database='greenhouse_data', user='root', password='rJ@mJ@r7')
		cursor = conn.cursor(buffered=True)

		query = "Select status from manual_controls"

		cursor.execute(query)
		statuses = cursor.fetchall()
		data["big_fan"] = (statuses[0][0])
		data["little_fan"] = (statuses[1][0])
		data["water"] = (statuses[2][0])
	except Error as e:
		print(e)
	finally:
		conn.close()
		cursor.close()
		return data


# returns False if there has not been a token assigned, or the wrong token is given
@app.route("/getTokens", methods = ["POST"])
def getToken():
	username = request.form.get("username", None)
	password = request.form.get("password", None)
	if username != None and password != None:

		currentUser = User(username, password)
		if currentUser.isValid():
			token = uuid4()
			currentUser.updateID(token)
			return jsonify({"token" : str(token)})
		else:
			return jsonify({"token" : "Invalid"})
	else:
		return jsonify({"token" : "Failed"})

@app.route("/sendCredentials", methods=["POST"])
def createUser():
	username = request.form.get("username", None)
	password = request.form.get("password", None)
	if username != None and password != None:
		newUser = User(username, password)
		newUser.signUp()
		token = uuid4()
		newUser.updateID(token)
		return jsonify({"token" : str(token)})
	else:
		return jsonify({"token" : "It didnt work"})

@app.route("/authCheck")
def authCheck():
	if checkAuth():
		return "valid"
	else:
		return "invalid"

@app.route("/")
def home():
	return "<h1>Up and Running! Hi Everyone :)</h1>"

@app.route("/getCurrentTemperatures", methods = ["GET"])
def getCurrentTemperatures():
	if checkAuth():

		tempIBCVal = select_recent_data("temperature","IBC_temperature")[1]
		tempInVal = select_recent_data("temperature","inside_temperature")[1]
		tempOutVal = select_recent_data("temperature","outside_temperature")[1]
		tempCompostVal = select_recent_data("temperature","mulch_temperature")[1]
		return jsonify(tempIBC=tempIBCVal, tempIn=tempInVal, tempOut=tempOutVal, tempCompost=tempCompostVal)
	else:
		return jsonify({"message": "string"})

@app.route("/getCurrentHumidity", methods = ["GET"])
def getCurrentHumidity():
	if checkAuth():
		currentHumidity = select_recent_data("humidity","humidity")[1]
		return jsonify(humidity=currentHumidity)
	else:
		return "Invalid AuthToken"

@app.route("/getCurrentStatuses", methods = ["GET"])
def getCurrentStatuses():
	if checkAuth():
		statuses = select_all_statuses()
		return jsonify(statuses)
	else:
		return "Invalid AuthToken"

# this function will handle get and post requests involving parameters
@app.route("/parameters", methods = ["GET", "POST"])
def parameters():
	if checkAuth(): #checkAuth()
		if request.method == 'POST':

		# the request body will have to be formatted very specifically:
		# Every parameter that wants to be changed will be put in a list defined by the parameters key
			params = request.form.get("parameters", None)
		# Every value will be put int a list defined by the values key
			vals = request.form.get("values")

			if not isinstance(params, list):
				params = [str(params)]
				vals = [vals]
		# the input to update_parameters need to be lists, otherwise the function won't work
		# even if the input is just of length one, it needs to be in a list
			return update_parameters(params, vals)

		elif request.method  == 'GET':
		# if a get request is done, then json results from the database will be returned.
			data = get_parameters()
			return jsonify(data)
	else:
		return "Invalid AuthToken"
@app.route("/manualControls", methods = ["GET", "POST"])
def manualControls():
	if checkAuth():
		if request.method == "POST":
			system = request.form.get("system", None)
			status = request.form,get("status", None)
			return update_manual_controls(system, status)
		if request.method == "GET":
			return jsonify(get_manual_controls())
	else:
		return "Invalid AuthToken"

if __name__ == "__main__":
	app.run()

