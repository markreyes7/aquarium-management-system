from config import apply_dev_defaults, get_arduino_base_url, get_database_path
from init_db import init_database
from server import create_app


if __name__ == "__main__":
    apply_dev_defaults()
    init_database()

    app = create_app()

    print("Development backend")
    print(f"Database: {get_database_path()}")
    print(f"Arduino/mock target: {get_arduino_base_url()}")
    app.run(host="127.0.0.1", port=3002, debug=True)
