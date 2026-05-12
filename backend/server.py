from flask import Flask
from config import get_server_host, get_server_port
from db import close_db

from routes.maintenance import bp as maintenance_bp
from routes.environment import bp as environment_bp
from routes.water_parameters import bp as water_parameters_bp
from routes.tank_profile import bp as tank_profile_bp

def create_app():
    app = Flask(__name__)

    # DB connection cleanup
    app.teardown_appcontext(close_db)

    app.register_blueprint(maintenance_bp)
    app.register_blueprint(environment_bp)
    app.register_blueprint(water_parameters_bp)
    app.register_blueprint(tank_profile_bp)

    return app

if __name__== "__main__":
    app = create_app()
    app.run(host=get_server_host(), port=get_server_port(), debug=True)
