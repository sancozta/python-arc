#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import os
import pygal
from flaskext.mysql import MySQL
from flask import Flask, request, g, redirect, url_for, abort, render_template, flash, jsonify, json, Response
from pymysql.cursors import DictCursor
from functools import wraps

# CREATE THE APPLICATION INSTANCE :)
app = Flask(__name__) 

# LOAD CONFIG FROM THIS FILE , FLASKR.PY.
app.config.from_object(__name__) 

# MYSQL CONFIGURATIONS
app.config["MYSQL_DATABASE_HOST"]       = os.environ.get("DATABASE_HOST")
app.config["MYSQL_DATABASE_PORT"]       = os.environ.get("DATABASE_PORT")
app.config["MYSQL_DATABASE_DB"]         = os.environ.get("DATABASE_DB")
app.config["MYSQL_DATABASE_USER"]       = os.environ.get("DATABASE_USER")
app.config["MYSQL_DATABASE_PASSWORD"]   = os.environ.get("DATABASE_PASSWORD")

# INSTANCE MYSQL
mysql = MySQL(cursorclass=DictCursor)

# INIT MYSQL
mysql.init_app(app)

# VERIFICANDO USUARIOS AUTORIZACAO
def check_auth(username, password):
    return username == "admin" and password == "secret"

# CASO O USUARIO NAO PASSE NA AUTENTIFCACAO
def authenticate():
    return Response(
        json.dumps({ "message" : "No Authenticate" }), 
        401, 
        { "WWW-Authenticate": "Basic realm='Login Required'", "Content-Type": "application/json" }
    )

# VERIFICACAO DE AUTENTICACAO
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# FUNÇÃO QUE É EXECUTADA QUANDO UMA PÁGINA NÃO É ENCONTRADA
@app.errorhandler(404)
def not_found(e):
    return jsonify({ "message" : "Route Not Found Aplication" }), 404

# HOME PAGE
@app.route("/", methods=["GET"])
def index():
    return jsonify({ "message" : "Home Aplication" })

# SEARCH USERS
@app.route("/users", methods=["GET"])
@requires_auth
def search_user():
    if request.method == "GET" and request.args :
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute("select id, name, email, password, token, arduino, date_format(modernize, '%%d/%%m/%%Y %%H:%%i:%%s') as modernize from users where id = %s", request.args.get("id"))
            return jsonify(curs.fetchall())
        except:
            return jsonify({ "message" : "Error in Operation" })
    if request.method == "GET" :
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute("select id, name, email, password, token, arduino, date_format(modernize, '%d/%m/%Y %H:%i:%s') as modernize from users")
            return jsonify(curs.fetchall())
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# CREATE USER
@app.route("/users", methods=["POST"])
@requires_auth
def create_user():
    if request.method == "POST" and request.form:
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute(
                "insert into users (name, email, password, arduino) values( %s, %s, %s, %s )", 
                (
                    request.form.get("name"),
                    request.form.get("email"),
                    request.form.get("password"),
                    request.form.get("arduino")
                )
            )
            conn.commit()
            return jsonify({ "message" : "Create User Sucess" })
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# UPDATE USER
@app.route("/users", methods=["PUT"])
@requires_auth
def update_user():
    if request.method == "PUT" and request.form:
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute(
                "update users set name = %s, email = %s, password = %s, arduino = %s where id = %s", 
                (
                    request.form.get("name"),
                    request.form.get("email"),
                    request.form.get("password"),
                    request.form.get("arduino"),
                    request.form.get("id"),
                )
            )
            conn.commit()
            return jsonify({ "message" : "Update User Sucess" })
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# DELETE USER
@app.route("/users", methods=["DELETE"])
@requires_auth
def delete_user():
    if request.method == "DELETE" and request.form:
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute("delete from users where id = %s", request.form.get("id"))
            conn.commit()
            return jsonify({ "message" : "Delete User Sucess" })
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# REGISTRY LOGS
@app.route("/logs", methods=["POST"])
@requires_auth
def create_log():
    if request.method == "POST" and request.form:
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute("select id, ifnull(token,'0') as token , arduino from users where arduino = %s", request.form.get("arduino"))
            respon  = curs.fetchall()
            conn.commit()
            if respon and respon[0]["token"] != '1':
                curs.execute("insert into logs (users_id, arduino) values( %s, %s )", (respon[0]["id"], request.form.get("arduino")))
                conn.commit()
            return jsonify({ "message" : "Create Logs Sucess" })
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# SEARCH LOGS
@app.route("/logs/<string:users_id>", methods=["GET"])
@requires_auth
def search_log(users_id):
    if request.method == "GET":
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute("select id, users_id, arduino, date_format(registry, '%%d/%%m/%%Y %%H:%%i:%%s') as registry from logs where users_id = %s", users_id)
            return jsonify(curs.fetchall())
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# REGISTRY LOGS
@app.route("/login", methods=["POST"])
@requires_auth
def login():
    if request.method == "POST" and request.form:
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute("select id, name, email, password, token, arduino, date_format(modernize, '%%d/%%m/%%Y %%H:%%i:%%s') as modernize from users where email = %s and password = %s", (request.form.get("email"), request.form.get("password")))
            return jsonify(curs.fetchall())
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# SEARCH USER
@app.route("/users/<string:users_id>", methods=["GET"])
@requires_auth
def search_users_detalis(users_id):
    if request.method == "GET":
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute("select id, name, email, password, token, arduino, date_format(modernize, '%%d/%%m/%%Y %%H:%%i:%%s') as modernize from users where id = %s", users_id)
            return jsonify(curs.fetchall())
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })

# ACTIVE DETECTION
@app.route("/flag", methods=["PUT"])
@requires_auth
def update_flag():
    if request.method == "PUT" and request.form:
        try:
            conn    = mysql.connect()
            curs    = conn.cursor()
            curs.execute(
                "update users set token = %s where id = %s", 
                (
                    request.form.get("token"),
                    request.form.get("id"),
                )
            )
            conn.commit()
            return jsonify({ "message" : "Update Flag Sucess" })
        except:
            return jsonify({ "message" : "Error in Operation" })
    return jsonify({ "message" : "Home Aplication" })
