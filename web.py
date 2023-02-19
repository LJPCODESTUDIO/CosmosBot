import json
from flask import Flask, render_template
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    list = []
    with open('stories.json') as f:
        stories = json.load(f)
    length = len(stories)
    for i in range(1, length+1):
        list.append('https://stories.ljpcool.com/' + str(i))
    return render_template('index.html', links=list)


@app.route('/<ID>')
def story(ID):
    with open('stories.json') as f:
        stories = json.load(f)
    text = stories[ID]
    return render_template('story.html', content=text, id=ID)


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


def run():
    app.run(host='0.0.0.0', port='5000')

def web_start():
    t = Thread(target=run)
    t.start()

run()