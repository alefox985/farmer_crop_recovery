from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_login import LoginManager
import os
from algosdk.v2client import algod

app = Flask(__name__)
app.config['SECRET_KEY'] = '07e7fde20cd63588fb6ada33ab7dca536be2bb7dd74f060a096ed62c05f491ef'
db_local_path = (os.path.join(os.path.dirname(__file__), '../db/database_lavazza.db'))
db_uri = 'sqlite:///{}'.format(db_local_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
engine = create_engine(db_uri)
login_manager = LoginManager(app)
# Setup HTTP client w/guest key provided by PureStake
algod_token = 'su8XEC09HD1HIWUNzQBnY1DzH8sOPwHF36kwNJOh'
algod_address = 'https://testnet-algorand.api.purestake.io/ps2'
purestake_token = {'X-API-Key': algod_token,}
algodclient = algod.AlgodClient(algod_token, algod_address, purestake_token)

from farmer_crop_insurance import routes
