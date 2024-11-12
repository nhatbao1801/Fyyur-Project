# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import abort, render_template, request, flash, redirect, url_for
import logging
from logging import Formatter, FileHandler
from forms import *
from sqlalchemy import func
from models import Venue, Artist, Show
import ast
from config import app, db


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format = "EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    """Renders a template displaying all venues grouped by city and state."""
    data = []

    # Query to get venues with the count of upcoming shows
    locations = (
        db.session.query(
            Venue.state,
            Venue.city,
            Venue.id,
            Venue.name,
            func.count(Show.id).label('num_upcoming_shows')
        )
        .outerjoin(Show, (Show.venue_id == Venue.id) & (Show.start_time > datetime.now()))
        .group_by(Venue.state, Venue.city, Venue.id)
        .order_by(Venue.state, Venue.city)
        .all()
    )
    # Group venues by city and state
    unique_locations = {}
    for loc in locations:
        key = (loc.state, loc.city)
        if key not in unique_locations:
            unique_locations[key] = []
        unique_locations[key].append({
            'id': loc.id,
            'name': loc.name,
            'num_upcoming_shows': loc.num_upcoming_shows
        })
    # Prepare data for rendering
    for (state, city), venues in unique_locations.items():
        data.append({
            'city': city,
            'state': state,
            'venues': venues
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """
    Searches for venues based on a search term provided in a POST request.
    """
    search_term = request.form.get('search_term', '').lower()

    # Query to search venues and count upcoming shows
    search_results = (
        db.session.query(
            Venue.id,
            Venue.name,
            func.count(Show.id).label('num_upcoming_shows')
        )
        .outerjoin(Show, (Show.venue_id == Venue.id) & (Show.start_time > datetime.now()))
        .filter(Venue.name.ilike(f'%{search_term}%'))
        .group_by(Venue.id)
        .all()
    )

    data = [{
        'id': result.id,
        'name': result.name,
        'num_upcoming_shows': result.num_upcoming_shows
    } for result in search_results]

    response = {
        'count': len(search_results),
        'data': data
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """
    Displays the details of a specific venue with upcoming and past shows.
    """
    venue = Venue.query.get(venue_id)

    if not venue:
        return abort(404)

    # Query shows with artist information
    shows = (
        db.session.query(Show, Artist)
        .join(Artist, Show.artist_id == Artist.id)
        .filter(Show.venue_id == venue_id)
        .all()
    )

    upcoming_shows = []
    past_shows = []

    for show, artist in shows:
        show_data = {
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    data = {
        'id': venue.id,
        'name': venue.name,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website_link,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    """
    Creates a new venue record in the database based on submitted form data.
    """

    error = False
    form_data = request.form

    try:
        venue = Venue(
            name=form_data['name'],
            city=form_data['city'],
            state=form_data['state'],
            address=form_data['address'],
            phone=form_data['phone'],
            facebook_link=form_data['facebook_link'],
        )

        db.session.add(venue)
        db.session.commit()

        flash(f'Venue {form_data["name"]} was successfully listed!')

    except Exception as e:
        error = True
        db.session.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue could not be listed.')

    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """
    Deletes a venue from the database based on the provided venue ID.
    """
    err = False
    try:
        venue = db.session.get(Venue, venue_id)
        if not venue:
            flash('Venue not found.')
            return render_template('pages/venues.html')

        db.session.delete(venue)
        db.session.commit()

        flash('Venue successfully deleted.')

    except Exception as e:
        err = True
        db.session.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.session.close()

    if err:
        flash('An error occurred. Venue could not be deleted.')

    return render_template('pages/venues.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
  """Get list artists
  """
  data = db.session.query(Artist).all()
  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    """
    Searches for artists based on a search term provided in a POST request.
    """

    search_term = request.form.get('search_term', '').lower()
    search_results = Artist.query.filter(
        Artist.name.ilike(f'%{search_term}%')).all()

    data = [{
        'id': artist.id,
        'name': artist.name,
        'num_upcoming_shows': db.session.query(func.count(Show.id)).filter(
            Show.artist_id == artist.id, Show.start_time > datetime.now()).scalar()

    } for artist in search_results]

    response = {
        'count': len(search_results),
        'data': data
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """
    Displays the details of a specific artist with past and upcoming shows.
    """

    artist = db.session.get(Artist, artist_id)

    if not artist:
        return abort(404)

    shows = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id).all()

    past_shows = []
    upcoming_shows = []
    for show in shows:
        show_data = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_image_link': artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        if show.start_time < datetime.now():
            past_shows.append(show_data)
        else:
            upcoming_shows.append(show_data)
    genres = ast.literal_eval(artist.genres)
    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website_link,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    """
    Presents a pre-populated form for editing an artist's details.
    """
    form = ArtistForm()
    artist = db.session.get(Artist, artist_id)
    if not artist:
        return abort(404)
    if artist:
        form.name.data = artist.name
        form.genres.data = artist.genres
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.website_link.data = artist.website_link
        form.facebook_link.data = artist.facebook_link
        form.seeking_venue.data = artist.seeking_venue
        form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    """Editing an artist's
    """
    artist_data = request.form.to_dict()

    try:
        artist = db.session.get(Artist, artist_id)
        artist.name = artist_data.get('name')
        artist.city = artist_data.get('city')
        artist.state = artist_data.get('state')
        artist.phone = artist_data.get('phone')
        artist.website_link = artist_data.get('website_link')
        artist.facebook_link = artist_data.get('facebook_link')
        artist.image_link = artist_data.get('image_link')
        artist.seeking_venue = artist_data.get('seeking_venue', False)
        artist.seeking_description = artist_data.get('seeking_description')

        db.session.commit()
        flash('Artist ' + artist.name + ' was successfully updated!')

    except Exception as e:
        db.session.rollback()
        print(e)
        flash('An Error occurred: Artist could not be updated')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = db.session.get(Venue, venue_id)

    if venue:
        form = VenueForm(obj=venue)

        return render_template('forms/edit_venue.html', form=form, venue=venue)
    else:
        flash('Venue not found!')
        return redirect(url_for('pages/venues.html'))


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    """Editing an venue
    """

    venue = db.session.get(Venue, venue_id)

    if venue:
        try:
            venue_data = request.form.to_dict()
            venue.name = venue_data.get('name')
            venue.city = venue_data.get('city')
            venue.state = venue_data.get('state')
            venue.address = venue_data.get('address')
            venue.phone = venue_data.get('phone')
            venue.website_link = venue_data.get('website_link')
            venue.facebook_link = venue_data.get('facebook_link')
            venue.image_link = venue_data.get('image_link')
            venue.seeking_talent = venue_data.get('seeking_talent')
            venue.seeking_description = venue_data.get('seeking_description')

            db.session.commit()
            flash('Venue {} was successfully updated!'.format(venue.name))

        except Exception as e:
            db.session.rollback()
            print(e)
            flash('An Error occurred: Venue could not be updated')

        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        flash('Venue not found!')
        return None

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    """
    Handles the creation of a new Artist record.
    """
    error = False

    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        website_link = request.form['website_link']
        facebook_link = request.form['facebook_link']
        image_link = request.form['image_link']
        seeking_venue = 'seeking_venue' in request.form
        seeking_description = request.form['seeking_description']

        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=str(genres),
            website_link=website_link,
            facebook_link=facebook_link,
            image_link=image_link,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description
        )

        db.session.add(artist)
        db.session.commit()

    except Exception as e:
        error = True
        db.session.rollback()
        print(f"Error creating artist: {e}")

    finally:
        db.session.close()
        if error:
            flash(f'Error: Artist {name} could not be listed.')
        else:
            flash(f'Artist {name} was successfully listed!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  """
  Displays a list of upcoming shows at all venues.
  """

  today = datetime.now()
  upcoming_shows = db.session.query(Show).join(Artist).join(
      Venue).filter(Show.start_time > today).all()

  shows = [{
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
  } for show in upcoming_shows]

  return render_template('pages/shows.html', shows=shows)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  """
  Handles the creation of a new Show record.
  """
  error = False

  try:
    artist_id = int(request.form['artist_id'])
    venue_id = int(request.form['venue_id'])
    start_time = datetime.strptime(
        request.form['start_time'], '%Y-%m-%d %H:%M:%S')

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()

  except (ValueError, Exception) as e:
    error = True
    db.session.rollback()
    print(f"Error creating show: {e}")

  finally:
    db.session.close()
    flash('Show was successfully listed!' if not error else 'An error occurred. Show could not be listed.')

  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
