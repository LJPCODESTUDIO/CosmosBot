import pysos
from flask import Flask, render_template
from threading import Thread

#db = pysos.Dict('Stories')
#db['stories'] = {0:'blank'}

app = Flask('')

@app.route('/')
def home():
    list = []
    db = pysos.Dict('Stories')
    length = len(db['stories'])
    db.close
    for i in range(1, length+1):
        list.append('https://stories.ljpcool.com/' + str(i))
    return render_template('index.html', links=list)


@app.route('/<ID>')
def story(ID):
    db = pysos.Dict('Stories')
    text = db['stories'][str(ID)]
    db.close
    return render_template('story.html', content=text, id=ID)

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

def run():
    app.run(host='0.0.0.0', port='1168')

def web_start():
    t = Thread(target=run)
    t.start()