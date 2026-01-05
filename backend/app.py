from flask import Flask
from db import close_db

app = Flask(__name__)
app.teardown_appcontext(close_db)
