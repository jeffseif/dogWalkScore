#! /usr/bin/env python3

# Import

import dogWalkScore
from flask import Flask as Flask,\
                  jsonify as FlaskJSONify,\
                  render_template as FlaskRender,\
                  request as FlaskRequest

# Initialize

# Flask
app = Flask(__name__)
# Build graph
id2Node, id2Edge, id2Poi, id2Tree, graphIds = dogWalkScore.MySql2Graph()
# Create global croppedIds
global croppedIds
croppedIds = []

# Flask routing

@app.route('/')
def index():
    return FlaskRender('map.html')

@app.route('/findAddress')
def findAddress():

    # Grab address from url

    address = FlaskRequest.args.get('q', '')
    minutes = float(FlaskRequest.args.get('m', ''))

    # Process the address

    json = dogWalkScore.FindAddress(address, minutes, id2Node, id2Poi, graphIds, id2Tree)

    # Check for bad address

    if json is None:
        return FlaskJSONify({})

    # Update croppedIds

    croppedIds.clear()
    croppedIds.extend(json.get('croppedIds'))

    # JSONify it

    return FlaskJSONify(json)

@app.route('/routePOI')
def routePOI():

    # Grab startId/poiId from url

    startId = int(FlaskRequest.args.get('s', ''))
    poiId = int(FlaskRequest.args.get('p', ''))

    # Route to the POI

    json = dogWalkScore.RoutePOI(startId, poiId, croppedIds, id2Node, id2Edge, id2Poi)

    # JSONify it

    return FlaskJSONify(json)

@app.route('/about')
def about():
    return FlaskRender('about.html')

@app.route('/contact')
def contact():
    return FlaskRender('contact.html')

@app.route('/<other>')
def other(other):
    return about()

# Script

if __name__ == '__main__':

    # Run Flask in debug, port 8000

    app.run(debug = True, port = 5000, host = '0.0.0.0')
