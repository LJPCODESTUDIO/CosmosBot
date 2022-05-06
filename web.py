import pysos
from quart import Quart, render_template
from threading import Thread

app = Quart('')

@app.route('/')
async def home():
    return 'Hello World'

@app.route('/<ID>')
async def story(ID):
    db = pysos.Dict('DataBase')
    text = db['stories'][str(ID)]
    db.close
    return await render_template('story.html', content=text, id=ID)

def run():
    app.run(host='localhost', port='5000')

def web_start():
    t = Thread(target=run)
    t.start()