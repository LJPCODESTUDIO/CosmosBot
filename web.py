import pysos
from flask import Flask, render_template
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    list = []
    db = pysos.Dict('DataBase')
    length = len(db['stories'])
    db.close
    for i in range(1, length):
        list.append('http://localhost:5000/' + str(i))
    return render_template('index.html', links=list)


@app.route('/<ID>')
def story(ID):
    db = pysos.Dict('DataBase')
    text = db['stories'][str(ID)]
    db.close
    return render_template('story.html', content=text, id=ID)

def run():
    app.run(host='localhost', port='5000')

def web_start():
    t = Thread(target=run)
    t.start()