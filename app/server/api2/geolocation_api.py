# standard imports
import logging
import os

# third party imports
from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

# platform imports
from server import db
from server.utils.auth import requires_auth
from share.models.location import Location
from share.location.validate import valid_location_name, valid_coordinate
from share.location import osm
from share.location.enum import LocationExternalSourceEnum
from share import path

logg = logging.getLogger()

geolocation_blueprint = Blueprint('v2_geolocation', __name__)


def location_to_response_object(location):
    """Compiles a json api response from location object

    Parameters
    ----------
    location : Location
        a location object to transform

    Returns
    -------
    response_object : dict
        the http response formatted location object
    """
    response_object = {
        'message': 'location successfully added',
        'data': {
            'location': {
                'id': location.id,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'common_name': location.common_name,
                'path': str(location),
                LocationExternalSourceEnum.OSM.name: {},
                },
            },
        }
    try:
        place_id = location.get_custom(LocationExternalSourceEnum.OSM, 'place_id')
        osm_id = location.get_custom(LocationExternalSourceEnum.OSM, 'osm_id')
        response_object['data']['location'][LocationExternalSourceEnum.OSM.name]['place_id'] = place_id
        response_object['data']['location'][LocationExternalSourceEnum.OSM.name]['osm_id'] = osm_id
    except:
        pass

    return response_object



class LocationExternalAPI(MethodView):
    """Handles requests that operate on external location references

    Documentation is brief since it implmements standard flask blueprint interface
    """
    def get(self, ext_type, ext_id):
        """Returns the location entry matching an external reference type and its id
        """
        if ext_type == LocationExternalSourceEnum.OSM.name:
            location = Location.get_by_custom(LocationExternalSourceEnum.OSM, 'place_id', ext_id)
            if location == None:
                response_object = {
                    'message': 'No stored OSM location match on place_id {}'.format(ext_id),
                }
                return make_response(jsonify(response_object)), 404
            response_object = location_to_response_object(location)
            return make_response(jsonify(response_object)), 200

        else:
            response_object = {
                'message': 'Unknown external source name {}'.format(ext_type),
            }
            return make_response(jsonify(response_object)), 400


class LocationAPI(MethodView):
    """Handles requests that operate on external location references

    Documentation is brief since it implmements standard flask blueprint interface
    """

    # TODO: This method is too long and should be divided up for clarity
    def get(self, path_string):
        """Returns the location entry matching the path string
        """
        # split given path into array elements
        # validate that each part is a valid location name token
        path_parts = path.reverse_split(path_string)
        c = 0
        for path_part in path_parts:
            if path_part == '':
                break
            if valid_location_name(path_part):
                c += 1
        if c == 0:
            if not valid_location_name(path_part):
                response_object = {
                    'message': 'Invalid location path: {}'.format(common_name)
                }
                return make_response(jsonify(response_object)), 400
  

        # if one element is found, and if a path with more than one element is given
        # make sure all the elements in the hierarchy match
        common_name = path_parts[0]
        locations = Location.query.filter(Location.common_name==common_name).all()
        valid_locations = []
        valid = True
        while len(locations) > 0:
            location = locations.pop(0)
            location_step = location
            for part in path_parts:
                if location_step.parent == None:
                    if len(valid_locations) > 0:
                        valid = False
                    break
                # TODO: fuzzy match
                if part != location_step.common_name:
                    valid = False
                    break
                location_step = location_step.parent
            if valid:
                valid_locations.append(location)

        if len(valid_locations) == 0:
            response_object = {
                    'message': 'Location path {} not found'.format(path_string),
                }
            return make_response(jsonify(response_object)), 404

        response_object = {
            'search_string': common_name,
            'locations': []
                }
        for location in valid_locations:
            response_object['locations'].append({
                'id': location.id,
                'common_name': location.common_name,
                'path': str(location),
                'latitude': location.latitude,
                'longitude': location.longitude,
                }
                )

        return make_response(jsonify(response_object)), 200



    # TODO: This method is too long and should be divided up for clarity
    def post(self):
        """Commits the given location entry to the database.

        Will fail if the location name and path already exist, or if external reference already exists.
        """

        # get the input data
        post_data = request.get_json()
        latitude = post_data.get('latitude')
        longitude = post_data.get('longitude')
        common_name = post_data.get('common_name')
        response_object = None

        # check coordinates and name
        if not valid_coordinate(latitude, longitude):
            response_object = {
                'message': 'Invalid coordinate format',
            }
            return make_response(jsonify(response_object)), 400
        if not valid_location_name(common_name):
            response_object = {
                'message': 'Invalid location name',
            }
            return make_response(jsonify(response_object)), 400

        location = Location(common_name, latitude, longitude) 

        # if parent is given, check that it exists
        parent_location = None
        try:
            parent_id = post_data['parent_id']
            parent_location = Location.query.get(parent_id)
            if parent_location == None:
                response_object = {
                    'message': 'parent id {} does not match any objects'.format(parent_id),
                   }
                return make_response(jsonify(response_object)), 400
            location.set_parent(parent_location)
        except KeyError:
            pass
        except Exception as e:
            response_object = {
                'message': 'add new location failed: {}'.format(e),
               }
            return make_response(jsonify(response_object)), 500

        # if osm is given, check that the data is valid
        osm_data = post_data.get(LocationExternalSourceEnum.OSM.name)
        if osm_data != None:
            if not osm.valid_data(osm_data):
                response_object = {
                        'message': 'invalid osm extension data',
                       }
                return make_response(jsonify(response_object)), 400
            try:
                location.add_external_data(LocationExternalSourceEnum.OSM, osm_data)
            except Exception as e:
                response_object = {
                    'message': 'add external data failed: {}'.format(e),
                   }
                return make_response(jsonify(response_object)), 500

        # flush to database
        db.session.add(location)
        db.session.commit()
        db.session.flush()
     

        response_object = location_to_response_object(location)
        return make_response(jsonify(response_object)), 201



geolocation_blueprint.add_url_rule(
    '/geolocation/<path:path_string>',
    view_func=LocationAPI.as_view('v2_geolocation_local_view'),
    methods=['GET']
)

geolocation_blueprint.add_url_rule(
    '/geolocation/<string:ext_type>/<int:ext_id>/',
    view_func=LocationExternalAPI.as_view('v2_geolocation_local_external_view'),
    methods=['GET']
)

geolocation_blueprint.add_url_rule(
    '/geolocation/',
    view_func=LocationAPI.as_view('v2_geolocation_add_view'),
    methods=['POST']
)
