from flask import render_template, url_for, flash, redirect, request, session
from sqlalchemy_utils import create_database, database_exists
from farmer_crop_insurance import db, app, engine, bcrypt
from farmer_crop_insurance.modules import User, FieldData, TransactionList, FarmLocation, TransactionData, TokenAmount
from flask_login import login_user, current_user, logout_user
from algosdk import account, transaction, mnemonic
from datetime import datetime
from farmer_crop_insurance import algodclient


def reset_db():
    if not database_exists(engine.url):
        create_database(engine.url)
    db.drop_all()
    db.create_all()
    sk, pk = account.generate_account()
    user_admin = User(username='admin', password=bcrypt.generate_password_hash('coffee').decode('utf-8'), role='admin', private_key=sk, address=pk)
    new_token = TokenAmount(agri_drought=10, meteo_drought=10, heavy_rain=10, shower_rain=15, storm_rain=20)
    db.session.add(user_admin)
    db.session.add(new_token)
    db.session.commit()
    print('Database created')

# call just when needed
# reset_db()


@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('home_admin'))
        if current_user.role == 'farmer':
            return redirect(url_for('home_farmer'))
    if request.method == 'POST':
        form_data = request.form.to_dict()
        user = User.query.filter_by(username=form_data['username']).first()
        # supplier
        if user and bcrypt.check_password_hash(user.password, form_data['password']):
            login_user(user)
            flash('Login successful, welcome to farmer crop recovery!', 'success')
            if user.role == 'admin':
                return redirect(url_for('home_admin'))
            if user.role == 'farmer':
                return redirect(url_for('home_farmer'))
        else:
            flash('Login unsuccessful, please check your credentials and try again', 'danger')
            return render_template('login.html')
    if request.method == 'GET':
        return render_template('login.html')


@app.route("/home_admin", methods=['GET', 'POST'])
def home_admin():
    if current_user.is_authenticated and current_user.role == 'admin':
        if request.method == 'GET':
            user = User.query.filter_by(username=current_user.username).first()
            user_info = algodclient.account_info(user.address)
            amount = user_info['amount'] / 1000000
            return render_template('home_admin.html', public_key=user.address, amount=amount, rewarding=TokenAmount.query.first())
    else:
        return redirect(url_for('login'))


@app.route("/register_farmer", methods=['GET', 'POST'])
def register_farmer():
    if current_user.is_authenticated and current_user.role == 'admin':
        if request.method == 'GET':
            return render_template('register_farmer.html', farm_list=FarmLocation.query.all())
        if request.method == 'POST':
            form_data = request.form.to_dict()
            username_check = User.query.filter_by(username=form_data['username']).first()
            email_check = User.query.filter_by(email=form_data['email']).first()
            location_check = FarmLocation.query.filter_by(name=form_data['field_location']).first()
            if username_check:
                flash('This username is already taken! Please, verify your insertion', 'danger')
                return redirect(url_for('register_farmer'))
            if email_check:
                flash('This email is already taken! Please, verify your insertion', 'danger')
                return redirect(url_for('register_farmer'))
            else:
                if form_data['decision'] == '1':
                    temperature_threshold = location_check.temperature_threshold
                    humidity_threshold = location_check.humidity_threshold
                    rain_lower = location_check.rain_lower
                    rain_heavy = location_check.rain_heavy
                    rain_shower = location_check.rain_shower
                    rain_storm = location_check.rain_storm
                elif form_data['decision'] == '2':
                    if not form_data['temp'] or not form_data['hum'] or not form_data['rain_lower'] or not form_data['rain_heavy'] or not form_data['rain_shower'] or not form_data['rain_storm']:
                        flash('Please, enter all threshold values!', 'danger')
                        return redirect(url_for('register_farmer'))
                    else:
                        temperature_threshold = form_data['temp']
                        humidity_threshold = form_data['hum']
                        rain_lower = form_data['rain_lower']
                        rain_heavy = form_data['rain_heavy']
                        rain_shower = form_data['rain_shower']
                        rain_storm = form_data['rain_storm']
                sk, pk = account.generate_account()
                hashed_password = bcrypt.generate_password_hash(form_data['psw']).decode('utf-8')
                role = "farmer"
                new_user = User(email=form_data['email'], password=hashed_password, username=form_data['username'],
                                name=form_data['name'],
                                surname=form_data['surname'], role=role,
                                phone_number=form_data['phone_number'], field_location=form_data['field_location'],
                                private_key=sk, address=pk, temperature_threshold=temperature_threshold, humidity_threshold=humidity_threshold, rain_lower=rain_lower, rain_heavy=rain_heavy, rain_shower=rain_shower, rain_storm=rain_storm)
                db.session.add(new_user)
                db.session.commit()
                flash('The user account has been created!', 'success')
                return redirect(url_for('register_farmer'))
    else:
        return redirect(url_for('login'))


@app.route("/register_location", methods=['GET', 'POST'])
def register_location():
    if current_user.is_authenticated and current_user.role == 'admin':
        if request.method == 'GET':
            return render_template('register_location.html')
        if request.method == 'POST':
            form_data = request.form.to_dict()
            name_check = FarmLocation.query.filter_by(name=form_data['name']).first()
            if name_check:
                flash('This location name already exists! Please, verify your insertion', 'danger')
                return redirect(url_for('register_location'))
            new_location = FarmLocation(name=form_data['name'], geographic_coordinates=form_data['gcs'], temperature_threshold=form_data['temp'], humidity_threshold=form_data['hum'], rain_lower=form_data['rain_lower'], rain_heavy=form_data['rain_heavy'], rain_shower=form_data['rain_shower'], rain_storm=form_data['rain_storm'])
            db.session.add(new_location)
            db.session.commit()
            flash('Farm location registered!', 'success')
            return redirect(url_for('register_location'))
    else:
        return redirect(url_for('login'))


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/home_farmer", methods=['GET', 'POST'])
def home_farmer():
    if current_user.is_authenticated and current_user.role == 'farmer':
        if request.method == 'GET':
            user = User.query.filter_by(username=current_user.username).first()
            user_info = algodclient.account_info(user.address)
            amount = user_info['amount'] / 1000000
            return render_template('home_farmer.html', field_list=FieldData.query.filter_by(user_id=current_user.id).order_by(FieldData.id.desc()).limit(30), public_key=user.address, amount=amount)
        if request.method == 'POST':
            # insert data in the db
            token_quantity = TokenAmount.query.first()
            form_data = request.form.to_dict()
            field_data = FieldData(user_id=current_user.id, time=datetime.utcnow(), temperature=form_data['temperature'], humidity=form_data['humidity'], rain_mm=form_data['rain'], tx_reg=False)
            db.session.add(field_data)
            db.session.commit()
            drought = check_condition_1(field_data, current_user.temperature_threshold, current_user.humidity_threshold, current_user.rain_lower)
            rain = check_condition_2(field_data, current_user.rain_heavy, current_user.rain_shower, current_user.rain_storm)
            token_amount = 0
            type = ""
            if drought != 0 and rain == 0:
                if drought == 1:
                    token_amount += token_quantity.agri_drought
                    type += "Agricultural drought"
                    flash('You reached 10 days of agricultural drought!', 'success')
                if drought == 2:
                    token_amount += token_quantity.meteo_drought
                    type += "Meteorological drought"
                    flash('You reached 10 days of meteorological drought!', 'success')
                if drought == 3:
                    token_amount += token_quantity.agri_drought
                    token_amount += token_quantity.meteo_drought
                    type += "Agricultural and meteorological drought"
                    flash('You reached 10 days of high drought!', 'success')
            if rain != 0:
                if rain == 1:
                    token_amount += token_quantity.heavy_rain
                    type += "Heavy rain"
                    flash('You reached 10 days of heavy rain!', 'success')
                if rain == 2:
                    token_amount += token_quantity.shower_rain
                    type += "Shower rain"
                    flash('You reached 10 days of shower rain!', 'success')
                if rain == 3:
                    token_amount += token_quantity.storm_rain
                    type += "Storm rain"
                    flash('You reached 10 days of storm rain!', 'success')
            if token_amount > 0:
                transaction_request = TransactionList(username=current_user.username, user_id=current_user.id, address=current_user.address, amount=token_amount, time=datetime.utcnow(), tx_id="Transaction has not been executed", status="Waiting", type=type)
                db.session.add(transaction_request)
                db.session.commit()
                field = FieldData.query.filter_by(user_id=current_user.id).order_by(FieldData.id.desc()).limit(10)
                for row in field:
                    data = TransactionData(tx_id=transaction_request.id, user_id=row.user_id, time=row.time, temperature=row.temperature, humidity=row.humidity, rain_mm=row.rain_mm)
                    row.tx_reg = True
                    db.session.add(data)
                    db.session.commit()
                flash('The transaction request has been sent', 'success')
            return redirect(url_for('home_farmer'))
    else:
        return redirect(url_for('login'))


# checks high temperature, low humidity and no rain conditions
def check_condition_1(field_data, temperature_threshold, humidity_threshold, rain_lower_bounder):
    data = FieldData.query.filter_by(user_id=field_data.user_id, tx_reg=False).order_by(FieldData.id.desc()).limit(10)
    count_1 = 0
    count_2 = 0
    for row in data:
        if row.temperature >= temperature_threshold and row.humidity <= humidity_threshold:
            count_1 += 1
        if row.rain_mm <= rain_lower_bounder:
            count_2 += 1
    if count_1 == 10 and count_2 != 10:
        return 1
    if count_1 != 10 and count_2 == 10:
        return 2
    if count_1 == 10 and count_2 == 10:
        return 3
    else:
        return 0


# checks rain conditions
def check_condition_2(field_data, heavy_rain, shower_rain, storm_rain):
    data = FieldData.query.filter_by(user_id=field_data.user_id, tx_reg=False).order_by(FieldData.id.desc()).limit(10)
    count = 0
    tot_rain = 0
    for row in data:
        tot_rain += row.rain_mm
        count += 1
    if count < 10:
        return 0
    elif count == 10:
        mean = tot_rain / count
        if mean < shower_rain and mean >= heavy_rain:
            return 1
        if mean < storm_rain and mean >= shower_rain:
            return 2
        if mean >= storm_rain:
            return 3
        else:
            return 0


@app.route("/farmer_transaction_list", methods=['GET', 'POST'])
def farmer_transaction_list():
    if current_user.is_authenticated and current_user.role == 'farmer':
        if request.method == 'GET':
            return render_template('farmer_transaction_list.html', transaction_list=TransactionList.query.filter_by(user_id=current_user.id).order_by(TransactionList.id.desc()).all(), transaction_data=TransactionData.query.filter_by(user_id=current_user.id).order_by(TransactionData.id.desc()).all())
    else:
        return redirect(url_for('login'))


@app.route("/view_transactions", methods=['GET', 'POST'])
def view_transactions():
    if current_user.is_authenticated and current_user.role == 'admin':
        transaction_list = TransactionList.query.order_by(TransactionList.id.desc()).all()
        if request.method == 'GET':
            return render_template('view_transactions.html', transaction_list=transaction_list, transaction_data=TransactionData.query.order_by(TransactionData.id.desc()).all())
        if request.method == 'POST':
            for tx in transaction_list:
                if tx.status == 'Waiting':
                    if request.form['decision'] == 'Accept':
                        tx.status = 'Accepted'
                        tx_id = execute_transaction(tx.address, tx.amount)
                        tx.tx_id = tx_id
                        tx.time = datetime.utcnow()
                        db.session.commit()
                        flash('The transaction has been executed!', 'success')
                        break
                    if request.form['decision'] == 'Reject':
                        tx.status = 'Rejected'
                        db.session.commit()
                        break
            return redirect(url_for('view_transactions'))
    else:
        return redirect(url_for('login'))


def execute_transaction(receiver_pk, amount):
    # get suggested parameters from Algod
    params = algodclient.suggested_params()

    gh = params.gh
    first_valid_round = params.first
    last_valid_round = params.last
    fee = params.min_fee
    send_amount = amount
    sender = User.query.filter_by(username='admin').first()
    sender_pk = sender.address
    sender_sk = sender.private_key
    sender_account = sender_pk
    receiver_account = receiver_pk

    # Create and sign transaction
    tx = transaction.PaymentTxn(sender_account, fee, first_valid_round, last_valid_round, gh, receiver_account, send_amount, flat_fee=True)
    signed_tx = tx.sign(sender_sk)

    try:
        tx_confirm = algodclient.send_transaction(signed_tx)
        print('Transaction sent with ID', signed_tx.transaction.get_txid())
        wait_for_confirmation(algodclient, txid=signed_tx.transaction.get_txid())
    except Exception as e:
        print(e)
    return signed_tx.transaction.get_txid()


# Function from Algorand Inc.
def wait_for_confirmation(client, txid):
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print('Waiting for confirmation')
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print('Transaction confirmed in round', txinfo.get('confirmed-round'))
    return txinfo


@app.route("/change_password", methods=['GET', 'POST'])
def change_password():
    if current_user.is_authenticated:
        if request.method == 'GET':
            return render_template('change_password.html')
        if request.method == 'POST':
            form_data = request.form.to_dict()
            if bcrypt.check_password_hash(current_user.password, form_data['password']):
                current_password = form_data['password']
            else:
                flash('Wrong password, please retry.', 'danger')
                return redirect(url_for('change_password'))
            if form_data['psw'] == form_data['psw-repeat'] and form_data['psw'] != current_password:
                new_password = form_data['psw']
                new_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
                current_user.password = new_hash
                db.session.commit()
                flash('Your password has been updated!', 'success')
                if current_user.role == 'admin':
                    return redirect(url_for('home_admin'))
                if current_user.role == 'farmer':
                    return redirect(url_for('home_farmer'))
            else:
                flash('Password does not match, please retry.', 'danger')
                return redirect(url_for('change_password'))
    else:
        return redirect(url_for('login'))


@app.route("/token_amount", methods=['GET', 'POST'])
def token_amount():
    if current_user.is_authenticated and current_user.role == 'admin':
        if request.method == 'GET':
            return render_template('token_amount.html', actual_amount=TokenAmount.query.first())
        if request.method == 'POST':
            form_data = request.form.to_dict()
            token_quantity = TokenAmount.query.first()
            token_quantity.agri_drought = form_data['agri_drought']
            token_quantity.meteo_drought = form_data['meteo_drought']
            token_quantity.heavy_rain = form_data['heavy_rain']
            token_quantity.shower_rain = form_data['shower_rain']
            token_quantity.storm_rain = form_data['storm_rain']
            db.session.commit()
            return redirect(url_for('home_admin'))
    else:
        return redirect(url_for('login'))


@app.route("/about", methods=['GET', 'POST'])
def about():
    if current_user.is_authenticated and current_user.role == 'farmer':
        if request.method == 'GET':
            return render_template('about.html', rewarding=TokenAmount.query.first(), user=User.query.filter_by(id=current_user.id).first())
    else:
        return redirect(url_for('login'))


def set_flash_message():
    if session.get('flash_message'):
        flash(session.get('flash_message'))
        session.pop('flash_message')
