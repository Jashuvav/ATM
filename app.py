from datetime import datetime
from pprint import pprint

from flask import Flask, request, redirect, url_for, render_template, make_response

user_details = {}

app = Flask(__name__, template_folder='templets')


def get_current_user():
    user_email = request.cookies.get('UserId', '').strip()
    if not user_email:
        return None, None

    user_data = user_details.get(user_email)
    if not user_data:
        return None, None

    return user_email, user_data


def log_user_state(action, user_email=None):
    snapshot = {
        'action': action,
        'user_email': user_email, 
        'user_details': dict(user_details),
    }
    pprint(snapshot)


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/landing', methods=['GET'])
def landing():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('username', '').strip()
        user_email = request.form.get('email', '').strip()
        user_password = request.form.get('password', '').strip()
        user_confirmpassword = request.form.get('confirmpassword', '').strip()
        user_phone = request.form.get('phone', '').strip()

        if user_password != user_confirmpassword:
            return 'Password mismatch'
        if user_email not in user_details:
            user_details[user_email] = {
                'username': user_name,
                'userphone': user_phone,
                'userpassword': user_password,
                'Amount': 0,
                'transactions': [],
            }

            log_user_state('register', user_email)
            return redirect(url_for('login'))
        return 'User Already existed'
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_email = request.form.get('email', '').strip()
        login_password = request.form.get('password', '').strip()
        if login_email in user_details:
            stored_password = user_details[login_email]['userpassword']
            if stored_password == login_password:
                resp = make_response(redirect(url_for('dashboard')))
                resp.set_cookie('UserId', login_email)
                log_user_state('login', login_email)
                return resp
            return 'Invalid Password'
        return 'Invalid Email'
    return render_template('login.html')


@app.route('/dashboard', methods=['GET'])
def dashboard():
    user_email, user_data = get_current_user()
    cookie_data = dict(request.cookies)
    user_name = user_data.get('username', 'Guest') if user_data else 'Guest'
    return render_template('dashboard.html', user_email=user_email, user_name=user_name, cookie_data=cookie_data)


@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    user_email, user_data = get_current_user()
    if not user_email or not user_data:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('UserId', '', expires=0)
        return response

    if request.method == 'POST':
        amount_value = request.form.get('amount', '0')
        try:
            deposit_amount = int(amount_value)
        except ValueError:
            return 'Please enter a valid amount'

        if deposit_amount > 0:
            if deposit_amount % 100 == 0:
                if deposit_amount <= 1000000:
                    user_details[user_email]['Amount'] += deposit_amount
                    user_details[user_email]['transactions'].append({
                        'type': 'Deposit',
                        'amount': deposit_amount,
                        'status': 'Success',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    })
                    log_user_state('deposit', user_email)
                    return render_template(
                        'balance.html',
                        message='Deposit successful.',
                        email=user_email,
                        balance=user_details[user_email]['Amount']
                    )
                return 'Amount exceeded than 50000'
            return 'Amount should be multiple of 100'
        return 'Amount should be greater than 0'
    return render_template('deposit.html')


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    user_email, user_data = get_current_user()
    if not user_email or not user_data:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('UserId', '', expires=0)
        return response

    if request.method == 'POST':
        amount_value = request.form.get('amount', '0')
        try:
            withdraw_amount = int(amount_value)
        except ValueError:
            return 'Please enter a valid amount'

        if withdraw_amount > 0:
            if withdraw_amount % 100 == 0:
                if withdraw_amount <= user_details[user_email]['Amount']:
                    user_details[user_email]['Amount'] -= withdraw_amount
                    user_details[user_email]['transactions'].append({
                        'type': 'Withdraw',
                        'amount': withdraw_amount,
                        'status': 'Success',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    })
                    log_user_state('withdraw', user_email)
                    return render_template(
                        'balance.html',
                        message='Withdrawal successful.',
                        email=user_email,
                        balance=user_details[user_email]['Amount']
                    )
                
                return 'Insufficient balance'
            return 'Amount should be multiple of 100'
        return 'Amount should be greater than 0'
    return render_template('withdraw.html')


@app.route('/balance', methods=['GET'])
def balance():
    user_email, user_data = get_current_user()
    if not user_email or not user_data:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('UserId', '', expires=0)
        return response

    balance_amount = user_data['Amount']
    log_user_state('balance', user_email)
    return render_template('balance.html', email=user_email, balance=balance_amount)


@app.route('/logout', methods=['GET'])
def logout():
    user_email = request.cookies.get('UserId', '').strip()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('UserId', '', expires=0)
    log_user_state('logout', user_email or None)
    return response


@app.route('/statements', methods=['GET'])
def statements():
    user_email, user_data = get_current_user()
    if not user_email or not user_data:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('UserId', '', expires=0)
        return response

    transactions = user_data.get('transactions', [])
    return render_template('statements.html', transactions=transactions)


if __name__ == '__main__':
    app.run(use_reloader=True, debug=True)

