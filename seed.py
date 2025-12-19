from app import db, Package, City, Flight, Hotel, Activity, app

with app.app_context():
    db.drop_all()
    db.create_all()

    # Seed City
    goa = City.query.filter_by(name='Goa').first()
    if not goa:
        goa = City(name='Goa')
        db.session.add(goa)
        db.session.commit()
    cochin = City.query.filter_by(name='Cochin').first()
    if not cochin:
        cochin = City(name='Cochin')
        db.session.add(cochin)
        db.session.commit()

    # Seed Packages
    packages = [
        Package(name='Goa Beach Escape', destination='Goa', price=18999,
                duration='4D/3N', image='https://picsum.photos/300/200?1', type='Family'),
        Package(name='Manali Adventure', destination='Manali', price=15999,
                duration='5D/4N', image='https://picsum.photos/300/200?2', type='Adventure'),
        Package(name='Kerala Honeymoon', destination='Kerala', price=25999,
                duration='6D/5N', image='https://picsum.photos/300/200?3', type='Honeymoon')
    ]
    db.session.bulk_save_objects(packages)
    db.session.commit()

    # Seed Flights for Goa and Cochin
    flights = [
        Flight(city_id=goa.id, source_station='New Delhi', destination_station='Goa', price=6500,
               details='19:40 - 22:15 | 6E-2603 | Cabin: 7kg | Check-in: 15kg'),
        Flight(city_id=goa.id, source_station='Goa', destination_station='New Delhi', price=6500,
               details='09:00 - 11:30 | 6E-2604 | Cabin: 7kg | Check-in: 15kg'),
        Flight(city_id=goa.id, source_station='Cochin', destination_station='Goa', price=6000,
               details='08:00 - 10:30 | 6E-1234 | Cabin: 7kg | Check-in: 15kg'),
        Flight(city_id=goa.id, source_station='Goa', destination_station='Cochin', price=6000,
               details='18:00 - 20:30 | 6E-5678 | Cabin: 7kg | Check-in: 15kg')
    ]
    db.session.bulk_save_objects(flights)
    db.session.commit()

    # Remove all existing hotels for Goa before seeding
    Hotel.query.filter_by(city_id=goa.id).delete()
    db.session.commit()
    # Seed Hotels for Goa
    hotels = [
        Hotel(city_id=goa.id, name='Calux Joia Do Mar Resort', address='Calangute - Arpora Rd, Porba Vaddo, Prabhu wada, Calangute, Goa 403516', room_category='DELUXE ROOM', price=3500, meal='WITH BREAKFAST', details=''),
        Hotel(city_id=goa.id, name='Amara Grand Baga', address='Survey No 233, E & D, Calangute - Baga Rd, Baga, Calangute, Goa 403516', room_category='PREMIUM ROOM', price=4500, meal='WITH BREAKFAST', details='')
    ]
    db.session.bulk_save_objects(hotels)
    db.session.commit()

    # Remove any old "Free Airport Transfers" activity for Goa
    Activity.query.filter_by(city_id=goa.id, name='Free Airport Transfers').delete()
    db.session.commit()
    # Seed Activities for Goa with rates for 1-4 pax
    activities = [
        Activity(city_id=goa.id, name='AIRPORT PICK UP', type='pickup', rate_1=2000, rate_2=1000, rate_3=700, rate_4=600, price=2000, details='Airport pickup from Dabolim Airport to hotel'),
        Activity(city_id=goa.id, name='AIRPORT DROP', type='drop', rate_1=2000, rate_2=1000, rate_3=700, rate_4=600, price=2000, details='Airport drop from hotel to Dabolim Airport'),
        Activity(city_id=goa.id, name='NORTH GOA TOUR SIC', type='tour', rate_1=500, rate_2=500, rate_3=500, rate_4=500, price=500, details='North Goa sightseeing tour (SIC)'),
        Activity(city_id=goa.id, name='SOUTH GOA TOUR SIC', type='tour', rate_1=600, rate_2=600, rate_3=600, rate_4=600, price=600, details='South Goa sightseeing tour (SIC)'),
        Activity(city_id=goa.id, name='BOAT CRUISE RIDE', type='activity', rate_1=400, rate_2=400, rate_3=400, rate_4=400, price=400, details='Boat cruise ride on Mandovi River'),
        Activity(city_id=goa.id, name='SCUBA DIVING+WATERSPORTS', type='activity', rate_1=2000, rate_2=2000, rate_3=2000, rate_4=2000, price=2000, details='Scuba diving and watersports package')
    ]
    db.session.bulk_save_objects(activities)
    db.session.commit()

    print('Seed data inserted: cities, flights, hotels, activities, packages')
