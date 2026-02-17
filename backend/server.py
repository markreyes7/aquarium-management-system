from flask import Flask
from db import close_db

from routes.maintenance import bp as maintenance_bp
from routes.environment import bp as environment_bp

def create_app():
    app = Flask(__name__)

    # DB connection cleanup
    app.teardown_appcontext(close_db)

    app.register_blueprint(maintenance_bp)
    app.register_blueprint(environment_bp)

    return app

if __name__== "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=3001, debug=True)    