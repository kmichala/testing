from flask import Flask, request, render_template, make_response
from flask.ext.restful import Api, Resource, reqparse

import json
import string
import random
from datetime import datetime

# define our categories
CATEGORIES = ( 'shop', 'restaurant', 'bar', 'club' )

# load business data from disk, load into dictionary (key/value)
with open('businesses.json') as data:
    businesses = json.load(data)

#
# define some helper functions
#
def generate_id(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def error_if_business_not_found(business_id):
    if business_id not in businesses:
        message = "Business {} doesn't exist".format(business_id)    
        abort(404, message=message)

def filter_and_sort_businesses(q='', sort_by='category'):
    filter_function = lambda x: q.lower() in (
        x[1]['name'] + x[1]['description']).lower()
    filtered_businesses = filter(filter_function, businesses.items())
    key_function = lambda x: x[1][sort_by]
    return sorted(filtered_businesses, key=key_function, reverse=True)
        
def render_business_as_html(business):
    return render_template(
        'business.html',
         business=business,
         categories=reversed(list(enumerate(CATEGORIES))))

def render_business_list_as_html(businesses):
    return render_template(
        'businesses.html',
        businesses=businesses,
        categories=CATEGORIES)

def nonempty_string(x):
    s = str(x)
    if len(x) == 0:
        raise ValueError('string is empty')
    return s

#
# specify the data we need to create a new help request
#
new_business_parser = reqparse.RequestParser()
for arg in ['name', 'location', 'description']:
    new_business_parser.add_argument(
       arg, type=nonempty_string, required=True,
       help="'{}' is a required value".format(arg))

#
# specify the data we need to update an existing help request
# do we need this at all...?
#
update_business_parser = reqparse.RequestParser()
#update_business_parser.add_argument(
#    'category', type=int, default=CATEGORIES.index('shop'))

#
# specify the parameters for filtering and sorting help requests
#
query_parser = reqparse.RequestParser()
query_parser.add_argument(
    'q', type=str, default='')
query_parser.add_argument(
    'sort-by', type=str, choices=('category', 'name'), default='category')
        
#
# define our (kinds of) resources
#
class Business(Resource):
    def get(self, business_id):
        error_if_business_not_found(business_id)
        return make_response(
            render_business_as_html(businesses[business_id]), 200)
            
    def patch(self, business_id):
        error_if_business_not_found(business_id)
        business=businesses[business_id]
#        update = update_business_parser.parse_args()
        business['name'] = update['name']
        business['location'] = update['location']
        business['URL'] = update['URL']
        business['phone'] = update['phone']
        business['hours'] = update['hours']
        business['rating'] = update['rating']
        business['description'] = update['description']
        business['category'] = update['category']
        return make_response(
            render_business_as_html(business), 200)

class BusinessAsJSON(Resource):
    def get(self, business_id):
        error_if_business_not_found(business_id)
        return businesses[business_id]
    
class BusinessList(Resource):
    def get(self):
        query = query_parser.parse_args()
        return make_response(
            render_business_list_as_html(
                filter_and_sort_businesses(
                    q=query['q'], sort_by=query['sort-by'])), 200)

def post(self): 
    business = new_business_parser.parse_args()
#    business['category'] = CATEGORIES.index('shop')
    businesses[generate_id()] = business
    return make_response(
        render_business_list_as_html(
            filter_and_sort_businesses()), 201)

class BusinessListAsJSON(Resource):
    def get(self):
        return businesses

#
# assign URL paths to our resources
#
app = Flask(__name__)
api = Api(app)
api.add_resource(BusinessList, '/businesses')
api.add_resource(BusinessListAsJSON, '/businesses.json')
api.add_resource(Business, '/business/<string:business_id>')
api.add_resource(BusinessAsJSON, '/business/<string:business_id>.json')

# start the server
if __name__ == '__main__':
    app.run(debug=True)
