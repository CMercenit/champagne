from flask import Flask, render_template, request, redirect, url_for
from flaskext.markdown import Markdown
from datetime import datetime
import sys, getopt
import boto3
from botocore.config import Config

app = Flask("Champagne")
Markdown(app)
dynamodb = boto3.client('dynamodb', config=Config(region_name='us-east-1'))

@app.route("/")
def home():
    resp = dynamodb.scan(TableName='champagne')
    notesList = []
    for item in resp['Items']:
        notesList.append({'id': item['note_id']['S'], 'title': item['title']['S'], 'lastModifiedDate': item['lastModifiedDate']['S'], 'message': item['message']['S']})
    return render_template("home.html", notes=notesList)

@app.route("/addNote")
def addNote():
    return render_template("noteForm.html", headerLabel="New Note", submitAction="createNote", cancelUrl=url_for('home'))

@app.route("/createNote", methods=["post"])
def createNote():
    noteId = dynamodb.scan(TableName='champagne', Select='COUNT')['Count'] + 1

    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']

    dynamodb.put_item(TableName='champagne', Item={'note_id': {'S': str(noteId)}, 'title': {'S': noteTitle}, 'lastModifiedDate': {'S': lastModifiedDate}, 'message': {'S': noteMessage}})

    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/viewNote/<int:noteId>")
def viewNote(noteId):
    noteId = str(noteId)
    resp = dynamodb.get_item(TableName='champagne', Key={'note_id': {'S': str(noteId)}})
    note = {'id' : resp['Item']['note_id']['S'], 
            'title' : resp['Item']['title']['S'], 
            'lastModifiedDate' : resp['Item']['lastModifiedDate']['S'], 
            'message' : resp['Item']['message']['S']}
    return render_template("viewNote.html", note=note, submitAction="/saveNote")

@app.route("/editNote/<int:noteId>")
def editNote(noteId):
    noteId = str(noteId)
    resp = dynamodb.get_item(TableName='champagne', Key={'note_id': {'S': str(noteId)}})
    note = {'id' : resp['Item']['note_id']['S'], 
            'title' : resp['Item']['title']['S'], 
            'lastModifiedDate' : resp['Item']['lastModifiedDate']['S'], 
            'message' : resp['Item']['message']['S']}
    cancelUrl = url_for('viewNote', noteId=noteId)
    return render_template("noteForm.html", headerLabel="Edit Note", note=note, submitAction="/saveNote", cancelUrl=cancelUrl)

@app.route("/saveNote", methods=["post"])
def saveNote():
    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteId = str(int(request.form['noteId']))
    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']

    dynamodb.put_item(TableName='champagne', Item={'note_id': {'S': str(noteId)}, 'title': {'S': noteTitle}, 'lastModifiedDate': {'S': lastModifiedDate}, 'message': {'S': noteMessage}})
    
    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/deleteNote/<int:noteId>")
def deleteNote(noteId):
    dynamodb.delete_item(TableName='champagne', Key={'note_id': {'S': str(noteId)}})
    return redirect("/")

if __name__ == "__main__":
    debug = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:", ["debug"])
    except getopt.GetoptError:
        print('usage: main.py [-h 0.0.0.0] [-p 5000] [--debug]')
        sys.exit(2)

    port = "5000"
    host = "0.0.0.0"
    print(opts)
    for opt, arg in opts:
        if opt == '-p':
            port = arg
        elif opt == '-h':
            host = arg
        elif opt == "--debug":
            debug = True

    app.run(host=host, port=port, debug=debug)

