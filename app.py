from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///holidays.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


# ---------------- MODELS ---------------- #
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    destination = db.Column(db.String(50))
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    duration = db.Column(db.String(20))
    image = db.Column(db.String(200))
    type = db.Column(db.String(50))

class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    source_station = db.Column(db.String(100))
    destination_station = db.Column(db.String(100))
    price = db.Column(db.Integer)
    details = db.Column(db.Text)

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    details = db.Column(db.Text)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    details = db.Column(db.Text)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    travellers = db.Column(db.Integer)
    taxi_type = db.Column(db.String(50))
    room_type = db.Column(db.String(50))
    hotel_type = db.Column(db.String(50))
    persons = db.Column(db.Integer)
    status = db.Column(db.String(20), default='CONFIRMED')


# ---------------- ROUTES ---------------- #
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/packages')
def packages():
    destination = request.args.get('destination')
    pkg_type = request.args.get('type')

    query = Package.query

    if destination:
        query = query.filter(Package.destination.ilike(f"%{destination}%"))
    if pkg_type:
        query = query.filter(Package.type == pkg_type)

    packages = query.all()

    # For each package, calculate total price from DB for default items
    package_prices = {}
    import re
    for pkg in packages:
        city = City.query.filter_by(name=pkg.destination).first()
        total_price = 0
        if city:
            flights = Flight.query.filter_by(city_id=city.id).all()
            hotels = Hotel.query.filter_by(city_id=city.id).all()
            activities = Activity.query.filter_by(city_id=city.id).all()
            # Match itinerary logic: only onward and return flights, first hotel for all nights, all activities
            duration_str = pkg.duration or "4D/3N"
            match = re.match(r"(\d+)D", duration_str)
            num_days = int(match.group(1)) if match else 4
            from_city = request.args.get('from_city', 'New Delhi')
            # Onward flight (first day)
            onward_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == from_city.lower() and f.destination_station.lower() == pkg.destination.lower()), None)
            if onward_flight:
                total_price += onward_flight.price
            # Return flight (last day)
            return_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == pkg.destination.lower() and f.destination_station.lower() == from_city.lower()), None)
            if return_flight:
                total_price += return_flight.price
            # Hotels: use first hotel for all nights (num_days-1)
            if hotels:
                total_price += hotels[0].price * (num_days-1)
            # Activities: one per day
            for idx in range(num_days):
                if idx < len(activities):
                    total_price += activities[idx].price
            package_prices[pkg.id] = total_price
        else:
            package_prices[pkg.id] = pkg.price

    return render_template('packages.html', packages=packages, package_prices=package_prices)


from datetime import datetime, timedelta

@app.route('/package/<int:id>')
def package_detail(id):
    package = Package.query.get_or_404(id)
    # Get departure date and from_city from query string if present
    departure = request.args.get('departure')
    from_city = request.args.get('from_city', 'New Delhi')
    # Parse duration for dynamic days
    import re
    duration_str = package.duration or "4D/3N"
    match = re.match(r"(\d+)D", duration_str)
    num_days = int(match.group(1)) if match else 4

    # Calculate day labels for sidebar
    try:
        base_date = datetime.strptime(departure, "%Y-%m-%d") if departure else datetime.today()
    except Exception:
        base_date = datetime.today()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_labels = []
    for i in range(num_days):
        dt = base_date + timedelta(days=i)
        label = f"{dt.day} {months[dt.month-1]}, {weekdays[dt.weekday()]}"
        day_labels.append(label)
    # Calculate initial total price for visible items from DB
    city = City.query.filter_by(name=package.destination).first()
    initial_total_price = 0
    item_prices = {}
    hotel_names = []
    if city:
        flights = Flight.query.filter_by(city_id=city.id).all()
        hotels = Hotel.query.filter_by(city_id=city.id).all()
        activities = Activity.query.filter_by(city_id=city.id).all()
        # Ensure all days have keys, set missing to 0
        # Assign flights by direction
        for idx in range(1, num_days+1):
            if idx == 1:
                # Onward flight: from_city to destination
                onward_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == from_city.lower() and f.destination_station.lower() == package.destination.lower()), None)
                if onward_flight:
                    item_prices[f"flight-day{idx}"] = onward_flight.price
                    initial_total_price += onward_flight.price
                else:
                    item_prices[f"flight-day{idx}"] = 0
            elif idx == num_days:
                # Return flight: destination to from_city
                return_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == package.destination.lower() and f.destination_station.lower() == from_city.lower()), None)
                if return_flight:
                    item_prices[f"flight-day{idx}"] = return_flight.price
                    initial_total_price += return_flight.price
                else:
                    item_prices[f"flight-day{idx}"] = 0
            else:
                # No local/intermediate flights
                item_prices[f"flight-day{idx}"] = 0
        # Only generate hotel info for nights (num_days-1)
        # Use the same hotel for all days (first hotel in DB)
        for idx in range(1, num_days):
            if hotels:
                hotel = hotels[0]
                item_prices[f"hotel-day{idx}"] = hotel.price
                initial_total_price += hotel.price
                hotel_names.append(hotel.name)
            else:
                item_prices[f"hotel-day{idx}"] = 0
                hotel_names.append("No Hotel")
        for idx in range(1, num_days+1):
            if idx <= len(activities):
                item_prices[f"activity-day{idx}"] = activities[idx-1].price
                initial_total_price += activities[idx-1].price
            else:
                item_prices[f"activity-day{idx}"] = 0
    else:
        initial_total_price = package.price
        hotel_names = ["No Hotel"] * (num_days-1)
    print("DEBUG: item_prices =", item_prices)
    return render_template('package_detail.html', package=package, departure=departure, day_labels=day_labels, initial_total_price=initial_total_price, from_city=from_city, item_prices=item_prices, hotel_names=hotel_names, num_days=num_days)


@app.route('/api/hotel_price')
def hotel_price():
    hotel_name = request.args.get('name')
    city_name = request.args.get('city')
    hotel = None
    if hotel_name and city_name:
        city = City.query.filter_by(name=city_name).first()
        if city:
            hotel = Hotel.query.filter_by(name=hotel_name, city_id=city.id).first()
    if hotel:
        return jsonify({'price': hotel.price})
    return jsonify({'price': None})

@app.route('/book/<int:package_id>', methods=['GET', 'POST'])
def book(package_id):
    package = Package.query.get_or_404(package_id)

    if request.method == 'POST':
        booking = Booking(
            package_id=package.id,
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            travellers=request.form['travellers'],
            taxi_type=request.form['taxi_type'],
            room_type=request.form['room_type'],
            hotel_type=request.form['hotel_type'],
            persons=request.form['persons']
        )
        db.session.add(booking)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('booking.html', package=package)


from sqlalchemy import text

import os

@app.route('/debug/update_hotel_prices')
def debug_update_hotel_prices():
    city = City.query.filter_by(name='Goa').first()
    if not city:
        return "Goa city not found."
    updates = [
        ('Radisson Goa Candolim - Holidays Selections', 5000),
        ('Taj Exotica Resort & Spa', 8000),
        ('Holiday Inn Resort Goa', 6500)
    ]
    for name, price in updates:
        hotel = Hotel.query.filter_by(name=name, city_id=city.id).first()
        if hotel:
            hotel.price = price
    db.session.commit()
    return "Hotel prices updated for Goa."

@app.route('/debug/dbpath')
def debug_dbpath():
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    abs_path = os.path.abspath(db_path)
    return f"Flask is using database file: {abs_path}"

@app.route('/debug/tables')
def debug_tables():
    # List all table names
    tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
    output = []
    for t in tables:
        table_name = t[0]
        # Print schema
        schema = db.session.execute(text(f"SELECT sql FROM sqlite_master WHERE name='{table_name}';")).fetchone()
        output.append(f"<b>Table:</b> {table_name}<br><b>Schema:</b> {schema[0] if schema else 'N/A'}")
        # Print sample record
        try:
            sample = db.session.execute(text(f"SELECT * FROM {table_name} LIMIT 1;")).fetchone()
            output.append(f"<b>Sample record:</b> {sample}<br><br>")
        except Exception as e:
            output.append(f"<b>Error reading sample:</b> {e}<br><br>")
    return "<hr>".join(output)

if __name__ == "__main__":
    app.run(debug=True)
