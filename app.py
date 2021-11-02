from flask import Flask
from flask import request

app = Flask(__name__)

@app.route("/webhook")
def webhook():
    return request.args

@app.route("/")
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run()
