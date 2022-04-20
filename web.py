from flask import Flask, render_template
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return 'Hello World'

def create_site(text, ID):
    @app.route('/<ID>')
    def site(ID):
        return render_template('story.html', content=text, id=ID)
    return 'http://Totally_Real_Link_Not_Really/'  + str(ID)

def run():
    app.run(host='0.0.0.0')

def web_start():
    t = Thread(target=run)
    t.start()