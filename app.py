from flask import Flask
import config

def create_app():
    flask_app = Flask(__name__)
    return flask_app

app = create_app()
app.config.from_object(config)

if __name__=='__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
