import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import stripe

app = Flask(__name__)

# ---------------- MILJÖVARIABLER ----------------
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_admin_losenord')
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
DOMAIN_URL = os.environ.get('DOMAIN_URL', 'http://localhost:5000')
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_RECIPIENT = os.environ.get('MAIL_RECIPIENT', 'admin@example.com')

# ---------------- DATABASE ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bookings.db')
db = SQLAlchemy(app)

# ---------------- MAIL ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
mail = Mail(app)

# ---------------- MODELLER ----------------
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    is_booked = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return render_template('admin-login.html')

# ---------------- KUND ----------------
@app.route('/index', methods=['GET', 'POST'])
def index():
    selected_date = None
    availabilities = []
    if request.method == 'POST':
        selected_date = request.form['date']
        availabilities = Availability.query.filter_by(date=selected_date, is_booked=False).all()
    return render_template('index.html', availabilities=availabilities, selected_date=selected_date, stripe_public_key=STRIPE_PUBLIC_KEY)

# ---------------- CREATE CHECKOUT SESSION ----------------
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    slot_id = request.form['slot_id']
    name = request.form['name']
    slot = Availability.query.get(slot_id)

    if not slot or slot.is_booked:
        return "Den här tiden är inte längre tillgänglig.", 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'sek',
                    'product_data': {'name': f"Bokning {slot.date} {slot.time}"},
                    'unit_amount': 25000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{DOMAIN_URL}/payment-success?slot_id={slot_id}&name={name}",
            cancel_url=f"{DOMAIN_URL}/index"
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)

# ---------------- PAYMENT SUCCESS ----------------
@app.route('/payment-success')
def payment_success():
    slot_id = request.args.get('slot_id')
    name = request.args.get('name')
    slot = Availability.query.get(slot_id)
    if not slot or slot.is_booked:
        return "Den här tiden är inte längre tillgänglig.", 400

    new_booking = Booking(name=name, date=slot.date, time=slot.time)
    slot.is_booked = True
    db.session.add(new_booking)
    db.session.commit()

    try:
        msg_admin = Message(
            subject=f"Ny bokning: {name}",
            sender=MAIL_USERNAME,
            recipients=[MAIL_RECIPIENT],
            body=f"{name} har bokat {slot.date} kl {slot.time}."
        )
        mail.send(msg_admin)
    except Exception as e:
        print("E-post kunde inte skickas:", e)

    return render_template('confirmation.html', name=name, date=slot.date, time=slot.time)

# ---------------- ADMIN ----------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == os.environ.get('ADMIN_EMAIL', 'mh5336363@gmail.com') and password == os.environ.get('ADMIN_PASSWORD', 'admin123'):
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            return "Fel e-post eller lösenord!", 401
    return render_template('admin-login.html')

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    bookings = Booking.query.all()
    availabilities = Availability.query.all()
    return render_template('admin.html', bookings=bookings, availabilities=availabilities)

# ---------------- Lägg till tillgänglighet ----------------
@app.route('/add-availability', methods=['GET', 'POST'])
def add_availability():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    if request.method == 'POST':
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        break_start = request.form.get('break_start')
        break_end = request.form.get('break_end')
        slot_length = int(request.form['slot_length'])

        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        if break_start and break_end:
            break_start_dt = datetime.strptime(f"{date} {break_start}", "%Y-%m-%d %H:%M")
            break_end_dt = datetime.strptime(f"{date} {break_end}", "%Y-%m-%d %H:%M")
        else:
            break_start_dt = break_end_dt = None

        current = start_dt
        while current < end_dt:
            slot_end = current + timedelta(minutes=slot_length)
            if break_start_dt and break_end_dt and (current >= break_start_dt and current < break_end_dt):
                current = break_end_dt
                continue
            if slot_end <= end_dt:
                time_str = current.strftime("%H:%M") + " - " + slot_end.strftime("%H:%M")
                if not Availability.query.filter_by(date=date, time=time_str).first():
                    db.session.add(Availability(date=date, time=time_str))
            current += timedelta(minutes=slot_length)

        db.session.commit()
        return redirect('/admin')
    return render_template('add-availability.html')

# ---------------- DELETE AVAILABILITY ----------------
@app.route('/delete-availability/<int:id>')
def delete_availability(id):
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    slot = Availability.query.get(id)
    if slot and not slot.is_booked:
        db.session.delete(slot)
        db.session.commit()
    return redirect('/admin')

# ---------------- DELETE BOOKING ----------------
@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')
    booking = Booking.query.get(id)
    if booking:
        slot = Availability.query.filter_by(date=booking.date, time=booking.time).first()
        if slot:
            slot.is_booked = False
        db.session.delete(booking)
        db.session.commit()
    return redirect('/admin')

# ---------------- LOGOUT ----------------
@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
§