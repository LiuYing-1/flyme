from flask import Flask
from flask import request
import json
app = Flask(__name__)

@app.route("/webhook", methods=['POST', 'GET'])
def webhook():
    params = json.loads(request.data.decode('utf-8'))
    print(params)
    return params 


@app.route("/")
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run()
