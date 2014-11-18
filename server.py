from flask import Flask, request, render_template, make_response
from flask.ext.restful import Api, Resource, reqparse

import json
import string
import random
from datetime import datetime

# define our categories
CATEGORIES = ( 'shopping', 'restaurant', 'nightlife' )

# load business data from disk, load into dictionary (key/value)
with open('business.json') as data:
    businesses = json.load(data)

#
# define some helper functions
#
def generate_id(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def error_if_business_not_found(business_id):
    if business_id not in businesses:
        message = "Business {} doesn't exist".format(business_id)    
        abort(404, message)

def filter_and_sort_businesses(q='', sort_by='category'):
    filter_function = lambda x: q.lower() in (
        x[1]['name'] + x[1]['description']).lower()
    filtered_helprequests = filter(filter_function, businesses.items())
    key_function = lambda x: x[1][sort_by]
    return sorted(filtered_helprequests, key=key_function, reverse=True)
        
def render_business_as_html(business):
    return render_template(
        'business.html',
        business=business,
        categories=reversed(list(enumerate(CATEGORIES))))
    
def render_helprequest_list_as_html(helprequests):
    return render_template(
        'helprequests.html',
        helprequests=helprequests,
        priorities=PRIORITIES)

def nonempty_string(x):
    s = str(x)
    if len(x) == 0:
        raise ValueError('string is empty')
    return s

#
# specify the data we need to create a new help request
#
new_helprequest_parser = reqparse.RequestParser()
for arg in ['from', 'title', 'description']:
    new_helprequest_parser.add_argument(
        arg, type=nonempty_string, required=True,
        help="'{}' is a required value".format(arg))

#
# specify the data we need to update an existing help request
#
update_helprequest_parser = reqparse.RequestParser()
update_helprequest_parser.add_argument(
    'priority', type=int, default=PRIORITIES.index('normal'))
update_helprequest_parser.add_argument(
    'comment', type=str, default='')

#
# specify the parameters for filtering and sorting help requests
#
query_parser = reqparse.RequestParser()
query_parser.add_argument(
    'q', type=str, default='')
query_parser.add_argument(
    'sort-by', type=str, choices=('priority', 'time'), default='time')
        
#
# define our (kinds of) resources
#
class HelpRequest(Resource):
    def get(self, helprequest_id):
        error_if_helprequest_not_found(helprequest_id)
        return make_response(
            render_helprequest_as_html(helprequests[helprequest_id]), 200) #gives the (a dictionary) we need 2 lists and two single item class definitions; start by just implementing GET methods

    def patch(self, helprequest_id):
        error_if_helprequest_not_found(helprequest_id)
        helprequest=helprequests[helprequest_id]
        update = update_helprequest_parser.parse_args()
        helprequest['priority'] = update['priority']
        if len(update['comment'].strip()) > 0:
            helprequest.setdefault('comments', []).append(update['comment'])
        return make_response(
            render_helprequest_as_html(helprequest), 200)

class HelpRequestAsJSON(Resource):
    def get(self, helprequest_id):
        error_if_helprequest_not_found(helprequest_id)
        return helprequests[helprequest_id]
    
class HelpRequestList(Resource):
    def get(self):
        query = query_parser.parse_args()
        return make_response(
            render_helprequest_list_as_html(
                filter_and_sort_helprequests(
                    q=query['q'], sort_by=query['sort-by'])), 200)

    def post(self):
        helprequest = new_helprequest_parser.parse_args()
        helprequest['time'] = datetime.isoformat(datetime.now())
        helprequest['priority'] = PRIORITIES.index('normal')
        helprequests[generate_id()] = helprequest
        return make_response(
            render_helprequest_list_as_html(
                filter_and_sort_helprequests()), 201)

class HelpRequestListAsJSON(Resource):
    def get(self):
        return helprequests

#
# assign URL paths to our resources
#
app = Flask(__name__)
api = Api(app)
api.add_resource(HelpRequestList, '/requests')
api.add_resource(HelpRequestListAsJSON, '/requests.json')
api.add_resource(HelpRequest, '/request/<string:helprequest_id>')
api.add_resource(HelpRequestAsJSON, '/request/<string:helprequest_id>.json')

# start the server
if __name__ == '__main__':
    app.run(debug=True)
