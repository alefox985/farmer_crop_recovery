from farmer_crop_insurance import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class FarmLocation(db.Model):
    __tablename__ = 'farm_location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    geographic_coordinates = db.Column(db.String(60))
    temperature_threshold = db.Column(db.Float)
    humidity_threshold = db.Column(db.Float)
    rain_lower = db.Column(db.Float)
    rain_heavy = db.Column(db.Float)
    rain_shower = db.Column(db.Float)
    rain_storm = db.Column(db.Float)
    user = db.relationship('User')

    def __repr__(self):
        return f"FarmLocation('{self.name}', '{self.geographic_coordinates}', '{self.temperature_threshold}', '{self.humidity_threshold}', '{self.rain_mm_threshold}')"


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(60))
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True)
    phone_number = db.Column(db.String(50))
    role = db.Column(db.String(50))
    field_location = db.Column(db.String(60), db.ForeignKey('farm_location.name'))
    private_key = db.Column(db.String(120))
    address = db.Column(db.String(100))
    temperature_threshold = db.Column(db.Float)
    humidity_threshold = db.Column(db.Float)
    rain_lower = db.Column(db.Float)
    rain_heavy = db.Column(db.Float)
    rain_shower = db.Column(db.Float)
    rain_storm = db.Column(db.Float)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.phone_number}', '{self.role}')"


class FieldData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rain_mm = db.Column(db.Float)
    tx_reg = db.Column(db.Boolean)

    def __repr__(self):
        return f"FieldData('{self.temperature}', '{self.humidity}', '{self.rain_mm}')"


class TransactionList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    user_id = db.Column(db.Integer)
    address = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    time = db.Column(db.DateTime)
    tx_id = db.Column(db.String(50))
    status = db.Column(db.String(50))
    type = db.Column(db.String(100))

    def __repr__(self):
        return f"TransactionList('{self.id}', '{self.username}', '{self.user_id}', '{self.address}', '{self.amount}', '{self.time}')"


class TransactionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rain_mm = db.Column(db.Float)

    def __repr__(self):
        return f"TransactionData('{self.user_id}', '{self.time}', '{self.temperature}', '{self.humidity}', '{self.rain_mm}')"


class TokenAmount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agri_drought = db.Column(db.Integer)
    meteo_drought = db.Column(db.Integer)
    heavy_rain = db.Column(db.Integer)
    shower_rain = db.Column(db.Integer)
    storm_rain = db.Column(db.Integer)

    def __repr__(self):
        return f"TokenAmount('{self.user_id}')"
