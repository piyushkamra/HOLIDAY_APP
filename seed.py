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
        Flight(city_id=goa.id, source_station='Cochin', destination_station='Goa', price=6000,
               details='08:00 - 10:30 | 6E-1234 | Cabin: 7kg | Check-in: 15kg'),
        Flight(city_id=goa.id, source_station='Goa', destination_station='Cochin', price=6000,
               details='18:00 - 20:30 | 6E-5678 | Cabin: 7kg | Check-in: 15kg')
    ]
    db.session.bulk_save_objects(flights)
    db.session.commit()

    # Seed Hotels for Goa
    hotels = [
        Hotel(city_id=goa.id, name='Radisson Goa Candolim - Holidays Selections', price=18000,
              details='Executive Room | Breakfast included | Free stay for kid'),
        Hotel(city_id=goa.id, name='Taj Exotica Resort & Spa', price=22000,
              details='Luxury Room | Breakfast & Dinner | Sea View'),
        Hotel(city_id=goa.id, name='Holiday Inn Resort Goa', price=16000,
              details='Deluxe Room | Breakfast included | Pool Access')
    ]
    db.session.bulk_save_objects(hotels)
    db.session.commit()

    # Seed Activities for Goa
    activities = [
        Activity(city_id=goa.id, name='Free Airport Transfers', price=0,
                 details='Enjoy free transfers in a comfortable private vehicle from the Airport to the hotel.'),
        Activity(city_id=goa.id, name='Water Sports at Baga Beach', price=2000,
                 details='Enjoy parasailing, jet ski, and banana boat rides at Baga Beach.'),
        Activity(city_id=goa.id, name='Sunset Cruise on Mandovi River', price=1200,
                 details='Enjoy a scenic sunset cruise with music and dance on the Mandovi River.')
    ]
    db.session.bulk_save_objects(activities)
    db.session.commit()

    print('Seed data inserted: cities, flights, hotels, activities, packages')
