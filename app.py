from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
import os
db_path = os.path.abspath("HOLIDAY_APP/instance/holidays.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
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
    address = db.Column(db.Text)
    room_category = db.Column(db.String(100))
    price = db.Column(db.Integer)
    meal = db.Column(db.String(100))
    details = db.Column(db.Text)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    name = db.Column(db.String(100))
    type = db.Column(db.String(50))  # e.g., pickup, drop, tour
    rate_1 = db.Column(db.Integer)   # rate for 1 pax
    rate_2 = db.Column(db.Integer)   # rate for 2 pax
    rate_3 = db.Column(db.Integer)   # rate for 3 pax
    rate_4 = db.Column(db.Integer)   # rate for 4 pax
    price = db.Column(db.Integer)    # default price (optional)
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
    print("DEBUG: packages found =", len(packages))

    # For each package, calculate both "With Flight" and "Without Flight" prices
    package_prices = {}
    import re
    for pkg in packages:
        city = City.query.filter_by(name=pkg.destination).first()
        price_with_flight = 0
        price_without_flight = 0
        if city:
            flights = Flight.query.filter_by(city_id=city.id).all()
            hotels = Hotel.query.filter_by(city_id=city.id).order_by(Hotel.id).all()
            activities = Activity.query.filter_by(city_id=city.id).all()
            duration_str = pkg.duration or "4D/3N"
            match = re.match(r"(\d+)D", duration_str)
            num_days = int(match.group(1)) if match else 4
            from_city = request.args.get('from_city', 'New Delhi')
            # Onward flight (first day)
            onward_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == from_city.lower() and f.destination_station.lower() == pkg.destination.lower()), None)
            if onward_flight:
                price_with_flight += onward_flight.price
            # Return flight (last day)
            return_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == pkg.destination.lower() and f.destination_station.lower() == from_city.lower()), None)
            if return_flight:
                price_with_flight += return_flight.price
            # Hotels: use first hotel for all nights (num_days-1)
            if hotels:
                price_with_flight += hotels[0].price * (num_days-1)
                price_without_flight += hotels[0].price * (num_days-1)
            # Activities: assign dynamically by type, Goa special case
            pickup_acts = [a for a in activities if a.type and a.type.lower() == "pickup"]
            drop_acts = [a for a in activities if a.type and a.type.lower() == "drop"]
            tour_acts = [a for a in activities if a.type and a.type.lower() == "tour"]

            day_activities = []
            num_middle_days = num_days - 2
            # Day 1: pickup
            day_activities.append(pickup_acts)
            # Special case for Goa: assign all tours to day 3
            if pkg.destination.lower() == "goa" and num_days == 4:
                day_activities.append([])  # day 2
                day_activities.append(tour_acts)  # day 3
            else:
                # Middle days: distribute tours, one per day, extra tours on last middle day
                for i in range(num_middle_days):
                    if len(tour_acts) == 0:
                        day_activities.append([])
                    elif len(tour_acts) <= num_middle_days:
                        if i < len(tour_acts):
                            day_activities.append([tour_acts[i]])
                        else:
                            day_activities.append([])
                    else:
                        if i < num_middle_days - 1:
                            day_activities.append([tour_acts[i]])
                        else:
                            day_activities.append(tour_acts[i:])
            # Last day: drop
            day_activities.append(drop_acts)
            # Get number of persons from query string, default to 1
            try:
                persons = int(request.args.get('persons', 1))
            except Exception:
                persons = 1

            # Helper to get correct rate for activity
            def get_activity_rate(activity, persons):
                if persons == 1 and hasattr(activity, "rate_1") and activity.rate_1 is not None:
                    return activity.rate_1
                elif persons == 2 and hasattr(activity, "rate_2") and activity.rate_2 is not None:
                    return activity.rate_2
                elif persons == 3 and hasattr(activity, "rate_3") and activity.rate_3 is not None:
                    return activity.rate_3
                elif persons == 4 and hasattr(activity, "rate_4") and activity.rate_4 is not None:
                    return activity.rate_4
                elif hasattr(activity, "price") and activity.price is not None:
                    return activity.price
                return 0

            for acts in day_activities:
                for activity in acts:
                    if activity:
                        rate = get_activity_rate(activity, persons)
                        price_with_flight += rate * persons if rate is not None else 0
                        price_without_flight += rate * persons if rate is not None else 0
            package_prices[pkg.id] = {
                "with_flight": price_with_flight,
                "without_flight": price_without_flight
            }
        else:
            package_prices[pkg.id] = {
                "with_flight": pkg.price,
                "without_flight": pkg.price
            }

    return render_template('packages.html', packages=packages, package_prices=package_prices)


from datetime import datetime, timedelta

@app.route('/package/<int:id>')
def package_detail(id):
    package = Package.query.get_or_404(id)
    # Get departure date and from_city from query string if present
    departure = request.args.get('departure')
    from_city = request.args.get('from_city', 'New Delhi')
    flight_option = request.args.get('flight_option', 'with')  # default to 'with'
    # Parse duration for dynamic days
    import re
    duration_str = package.duration or "4D/3N"
    match = re.match(r"(\d+)D", duration_str)
    num_days = int(match.group(1)) if match else 4

    # Get initial_price from query string if present
    try:
        initial_price_param = int(request.args.get('initial_price', 0))
    except Exception:
        initial_price_param = 0

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
    hotel_details = []
    activity_details = []
    if city:
        flights = Flight.query.filter_by(city_id=city.id).all()
        hotels = Hotel.query.filter_by(city_id=city.id).all()
        activities = Activity.query.filter_by(city_id=city.id).all()
        # Ensure all days have keys, set missing to 0
        # Assign flights by direction
        item_prices = {}
        hotel_names = []
        hotel_details = []
        activity_details = []

        # Add flight prices to item_prices for each day
        for idx in range(1, num_days+1):
            if idx == 1:
                onward_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == from_city.lower() and f.destination_station.lower() == package.destination.lower()), None)
                if onward_flight and flight_option != "without":
                    item_prices[f"flight-day{idx}"] = onward_flight.price
                else:
                    item_prices[f"flight-day{idx}"] = 0
            elif idx == num_days:
                return_flight = next((f for f in flights if f.source_station and f.destination_station and f.source_station.lower() == package.destination.lower() and f.destination_station.lower() == from_city.lower()), None)
                if return_flight and flight_option != "without":
                    item_prices[f"flight-day{idx}"] = return_flight.price
                else:
                    item_prices[f"flight-day{idx}"] = 0
            else:
                item_prices[f"flight-day{idx}"] = 0

        # Add hotel prices to item_prices for each night (num_days-1)
        for idx in range(1, num_days):
            if hotels:
                hotel = hotels[0]
                item_prices[f"hotel-day{idx}"] = hotel.price
                hotel_names.append(hotel.name)
                hotel_details.append({
                    "name": hotel.name,
                    "address": hotel.address,
                    "room_category": hotel.room_category,
                    "meal": hotel.meal,
                    "price": hotel.price
                })
            else:
                item_prices[f"hotel-day{idx}"] = 0
                hotel_names.append("No Hotel")
                hotel_details.append({
                    "name": "No Hotel",
                    "address": "",
                    "room_category": "",
                    "meal": "",
                    "price": 0
                })

        # Helper to get correct rate for activity
        def get_activity_rate(activity, persons):
            if persons == 1 and hasattr(activity, "rate_1") and activity.rate_1 is not None:
                return activity.rate_1
            elif persons == 2 and hasattr(activity, "rate_2") and activity.rate_2 is not None:
                return activity.rate_2
            elif persons == 3 and hasattr(activity, "rate_3") and activity.rate_3 is not None:
                return activity.rate_3
            elif persons == 4 and hasattr(activity, "rate_4") and activity.rate_4 is not None:
                return activity.rate_4
            elif hasattr(activity, "price") and activity.price is not None:
                return activity.price
            return 0

        # Assign activities to days dynamically by type, distributing tours
        pickup_acts = [a for a in activities if a.type and a.type.lower() == "pickup"]
        drop_acts = [a for a in activities if a.type and a.type.lower() == "drop"]
        tour_acts = [a for a in activities if a.type and a.type.lower() == "tour"]

        day_activities = []
        num_middle_days = num_days - 2
        # Day 1: pickup
        day_activities.append(pickup_acts)
        # Special case for Goa: custom distribution of tours, pickup/drop only on 1/4
        if package.destination.lower() == "goa" and num_days == 4:
            day_activities = []
            day_activities.append(pickup_acts)  # day 1: pickup only
            # Find activities by name
            def find_activity(name):
                return next((a for a in tour_acts if a.name.upper() == name.upper()), None)
            day_activities.append([find_activity("NORTH GOA TOUR SIC")])  # day 2
            day_activities.append([
                find_activity("SOUTH GOA TOUR SIC"),
                find_activity("BOAT CRUISE RIDE"),
                find_activity("SCUBA DIVING+WATERSPORTS")
            ])  # day 3
            day_activities.append(drop_acts)  # day 4: drop only
        else:
            # Middle days: distribute tours, one per day, extra tours on last middle day
            for i in range(num_middle_days):
                if len(tour_acts) == 0:
                    day_activities.append([])
                elif len(tour_acts) <= num_middle_days:
                    # Fewer or equal tours than middle days: assign one per day, empty if not enough
                    if i < len(tour_acts):
                        day_activities.append([tour_acts[i]])
                    else:
                        day_activities.append([])
                else:
                    # More tours than middle days: assign one per day, extras on last middle day
                    if i < num_middle_days - 1:
                        day_activities.append([tour_acts[i]])
                    else:
                        # Last middle day: assign remaining tours
                        day_activities.append(tour_acts[i:])
        # Last day: drop
        day_activities.append(drop_acts)

        # Get number of persons from query string, default to 1
        try:
            persons = int(request.args.get('persons', 1))
        except Exception:
            persons = 1

        for idx, acts in enumerate(day_activities, start=1):
            total_day_price = 0
            day_detail = []
            for activity in acts:
                if activity:
                    print(f"DEBUG: idx={idx}, activity_name={activity.name}, persons={persons}")
                    rate = get_activity_rate(activity, persons)
                    print(f"DEBUG: Multiplying rate {rate} by persons {persons} for activity {activity.name}")
                    total_day_price += rate * persons if rate is not None else 0
                    day_detail.append({
                        "name": activity.name,
                        "type": activity.type,
                        "rate_1": activity.rate_1,
                        "rate_2": activity.rate_2,
                        "rate_3": activity.rate_3,
                        "rate_4": activity.rate_4,
                        "details": activity.details
                    })
            item_prices[f"activity-day{idx}"] = total_day_price
            activity_details.append(day_detail if day_detail else [{
                "name": "",
                "type": "",
                "rate_1": 0,
                "rate_2": 0,
                "rate_3": 0,
                "rate_4": 0,
                "details": ""
            }])
    else:
        initial_total_price = package.price
        hotel_names = ["No Hotel"] * (num_days-1)
        hotel_details = [{
            "name": "No Hotel",
            "address": "",
            "room_category": "",
            "meal": "",
            "price": 0
        }] * (num_days-1)
        activity_details = [{
            "name": "",
            "type": "",
            "rate_1": 0,
            "rate_2": 0,
            "rate_3": 0,
            "rate_4": 0,
            "details": ""
        }] * num_days

    # Ensure initial_total_price is the sum of all item_prices values
    calculated_total_price = sum([v for v in item_prices.values() if isinstance(v, (int, float))])
    if initial_price_param > 0:
        initial_total_price = initial_price_param
    else:
        initial_total_price = calculated_total_price

    print("DEBUG: item_prices =", item_prices)
    print("DEBUG: activity_details =", activity_details)
    print("DEBUG: initial_total_price =", initial_total_price)
    return render_template(
        'package_detail.html',
        package=package,
        departure=departure,
        day_labels=day_labels,
        initial_total_price=initial_total_price,
        from_city=from_city,
        item_prices=item_prices,
        hotel_names=hotel_names,
        hotel_details=hotel_details,
        activity_details=activity_details,
        num_days=num_days,
        flight_option=flight_option,
        persons=persons
    )


@app.route('/api/hotels')
def api_hotels():
    city_name = request.args.get('city')
    hotels = []
    if city_name:
        city = City.query.filter_by(name=city_name).first()
        if city:
            hotels = Hotel.query.filter_by(city_id=city.id).all()
    hotel_names = [h.name for h in hotels]
    return jsonify({'hotels': hotel_names})

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

@app.route('/init_db')
def init_db():
    db.create_all()
    return "Database tables created."

if __name__ == "__main__":
    app.run(debug=True)
