#! /usr/bin/env python3

###
### Import
###

from json import loads as JSONLoad;
from math import pi as pi,\
                 sin as Sine,\
                 cos as Cosine,\
                 acos as ArcCosine;
from os.path import exists as Exists;
from pickle import dump as Pickle,\
                   load as UnPickle;
import sys;
###
# Maybe import MySql
###
try:
    from pymysql import connect as MySqlConnect;
except ImportError:
    pass;

###
### Constants
###

sys.setrecursionlimit(100000);
###
poiTypes = ('bar', 'restaurant');
poiType2Skip = {
    'bar' : (358, 409, 466),
    'restaurant' : (940, 1050),
};
###
# Walking constants
###
radiansPerDegree = pi / 180;
radiusOfEarth = 6371e3;
meterPerMin = 1.4 * 60;
meterPerLat = 111194.;
meterPerLng = 87882.;
###
worldLimits = {
    'latitudeMinimum' : 37.708,
    'latitudeMaximum' : 37.8125,
    'longitudeMinimum' : -122.515,
    'longitudeMaximum' : -122.355,
};
###
maximumTreePerMeter = 10;
maximumDistanceReduction = 0.3;

###
### Classes
###

class Address:
    def __init__(self, *args):
        self.address, self.latitude, self.longitude = args;
        ###
        return;

class Tree:
    def __init__(self, *args):
        if 4 == len(args):
            ###
            self.id, self.variety, latitude, longitude = args;
            self.latitude = self.longitude = None;
            if latitude is not None and longitude is not None:
                self.latitude = float(latitude);
                self.longitude = float(longitude);
        elif 5 == len(args):
            junk, id, variety, latitude, longitude = args;
            ###
            self.id = int(id);
            self.variety = variety.decode('latin-1');
            self.latitude = float(latitude);
            self.longitude = float(longitude);
        ###
        return;

class POI:
    def __init__(self, *args):
        if 4 == len(args):
            json, poiType, nodeIds, offsets = args;
            ###
            self.id = POIHash(json, poiType);
            self.poiType = poiType;
            self.name = json.get('name');
            ###
            self.nodeIds = nodeIds;
            self.offsets = offsets;
            ###
            location = json.get('location');
            latlng = location.get('latlng');
            ###
            self.latitude = self.longitude = None;
            if latlng is not None:
                self.latitude = latlng[0];
                self.longitude = latlng[1];
            ###
            self.address = location.get('address');
            self.city = location.get('city');
            self.state = location.get('state_code');
            ###
            self.imageUrl = json.get('image_url');
            self.yelpUrl = json.get('url');
            ###
        elif 12 == len(args):
            id, poiType, name, nodeIds, offsets, latitude, longitude, address, city, state, imageUrl, yelpUrl = args;
            ###
            self.id = int(id);
            self.poiType = poiType.decode('latin-1');
            self.name = name.decode('latin-1');
            self.nodeIds = bool(nodeIds) and list(int(nodeId) for nodeId in nodeIds.decode('latin-1').split(',') if nodeId) or [];
            self.offsets = bool(offsets) and list(float(offset) for offset in offsets.decode('latin-1').split(',') if offset) or [];
            self.latitude = float(latitude);
            self.longitude = float(longitude);
            self.address = address.decode('latin-1');
            self.city = city.decode('latin-1');
            self.state = state.decode('latin-1');
            self.imageUrl = imageUrl.decode('latin-1');
            self.yelpUrl = yelpUrl.decode('latin-1');
        ###
        return;
    ###
    def __hash__(self):
        return self.id;

class Node:
    def __init__(self, *args):
        if 1 == len(args):
            nodeXml, = args;
            ###
            self.id = self.longitude = self.latitude = self.label = None;
            ###
            for key, value in nodeXml.attrib.items():
                if 'id' == key:
                    self.id = int(value);
                elif 'lat' == key:
                    self.latitude = float(value);
                elif 'lon' == key:
                    self.longitude = float(value);
            ###
            self.count = 0;
            ###
            self.nodeIds = [];
            self.edgeIds = [];
            self.lengths = [];
            self.poiIds = [];
        elif 8 == len(args):
            ###
            id, isIntersection, latitude, longitude, nodeIds, edgeIds, lengths, poiIds = args;
            ###
            self.id = int(id);
            self.isIntersection = bool(isIntersection);
            self.latitude = float(latitude);
            self.longitude = float(longitude);
            self.nodeIds = bool(nodeIds) and list(int(nodeId) for nodeId in nodeIds.decode('latin-1').split(',') if nodeId) or [];
            self.edgeIds = bool(edgeIds) and list(int(edgeId) for edgeId in edgeIds.decode('latin-1').split(',') if edgeId) or [];
            self.lengths = bool(lengths) and list(float(length) for length in lengths.decode('latin-1').split(',') if length) or [];
            self.poiIds = bool(poiIds) and list(int(poiId) for poiId in poiIds.decode('latin-1').split(',') if poiId) or [];
        ###
        return;
    ###
    def __len__(self):
        return self.count;
    ###
    def __sub__(self, other):
        return LatLngDistance(self.latitude, self.longitude, other.latitude, other.longitude);
    ###
    def Count(self):
        self.count += 1;
        return;

class Edge:
    def __init__(self, *args):
        if 2 == len(args):
            xml, id2Node = args;
            ###
            self.id = int(xml.attrib.get('id'));
            ###
            self.name = None;
            for tag in xml.iter('tag'):
                key, value = (tag.attrib.get(moniker) for moniker in ('k', 'v'));
                if 'name' == key:
                    self.name = value;
            ###
            self.nodeIds = [int(nodeXml.attrib.get('ref')) for nodeXml in xml.iter('nd')];
            for nodeId in set(self.nodeIds):
                ###
                # Kick out unknown nodes
                ###
                if nodeId not in id2Node:
                    continue;
                ###
                id2Node.get(nodeId).Count();
            ###
            self.treeCount = 0;
        elif 4 == len(args):
            id, name, nodeIds, treeCount = args;
            ###
            self.id = int(id);
            self.name = name != b'None' and name.decode('latin-1') or '';
            self.nodeIds = bool(nodeIds) and list(int(nodeId) for nodeId in nodeIds.decode('latin-1').split(',') if nodeId) or [];
            self.treeCount = treeCount;
        elif 5 == len(args):
            junk, self.id, self.name, self.nodeIds, self.treeCount = args;
        ###
        return;

###
### Functions
###

def PrintNow(*arguments, sep = '\n', end = '\n'):
    from sys import stdout;
    ###
    print(*arguments, sep = sep, end = end);
    stdout.flush();
    ###
    return;

def GeoJSON(thing):
    if isinstance(thing, list):
        return [GeoJSON(element) for element in thing];
    ###
    geoJSON = {
        'type' : 'Feature',
        'geometry' : {
            'type' : 'Point',
            'coordinates' : [thing.longitude, thing.latitude],
        }
    };
    if isinstance(thing, Address):
        geoJSON.update({
            'properties' : {
                'title' : thing.address,
                'icon' : {
                    'clickable' : 'true',
                    'iconUrl' : './static/img/star-24.svg',
                    'iconSize' : [30, 30],
                },
            }
        });
    elif isinstance(thing, POI):
        iconUrl = {
            'bar' : './static/img/bar-24.svg',
            'park' : './static/img/park-24.svg',
            'restaurant' : './static/img/restaurant-24.svg',
        };
        ###
        geoJSON.update({
            'properties' : {
                'title' : thing.name,
                'icon' : {
                    'clickable' : 'true',
                    'iconUrl' : iconUrl[thing.poiType],
                    'iconSize' : [30, 30],
                },
                'imageUrl' : thing.imageUrl,
                'yelpUrl' : thing.yelpUrl,
            }
        });
    elif isinstance(thing, Tree):
        geoJSON.update({
            'properties' : {
                'title' : thing.variety,
                'icon' : {
                    'iconUrl' : './static/img/circle-24.svg',
                    'iconSize' : [12, 12],
                }
            }
        });
    ###
    return geoJSON;

def POIHash(json, poiType):
    latlng = json.get('location').get('latlng');
    ###
    return hash((json.get('id'), poiType, latlng and tuple(latlng) or ())) // 1000;

###
### Pre MySQL
###

def ReadOsmFile(osmFileName):
    import xml.etree.ElementTree as ET;
    ###
    PrintNow('Reading {:s} ... '.format(osmFileName), end = '');
    root = ET.parse(osmFileName).getroot();
    PrintNow('done');
    ###
    return root;

def InBounds(location):
    return worldLimits.get('latitudeMinimum') <= location.latitude <= worldLimits.get('latitudeMaximum') and \
           worldLimits.get('longitudeMinimum') <= location.longitude <= worldLimits.get('longitudeMaximum');

def ParseOSMNodes(osmRoot):
    PrintNow('Parsing OSM nodes ... ', end = '');
    id2Node = [Node(child) for child in osmRoot if 'node' == child.tag];
    ###
    # Throw out nodes which are out of bounds
    ###
    id2Node = {node.id : node for node in id2Node if InBounds(node)};
    PrintNow('found {:d}'.format(len(id2Node)));
    ###
    return id2Node;

def ParseOSMWays(osmRoot, id2Node):
    PrintNow('Parsing OSM ways ... ', end = '');
    id2Edge = [Edge(child, id2Node) for child in osmRoot if 'way' == child.tag];
    id2Edge = {edge.id : edge for edge in id2Edge};
    PrintNow('found {:d}'.format(len(id2Edge)));
    ###
    # Clean up edge names (non-latin-1 and ")
    ###
    for edge in id2Edge.values():
        edge.name = edge.name and edge.name.replace('–', '-').replace('"', '');
    ###
    return id2Edge;

def LinkNodes(nodeOne, nodeTwo, edge, id2Node):
    ###
    # Attach node
    ###
    nodeOne.nodeIds.append(nodeTwo.id);
    nodeTwo.nodeIds.append(nodeOne.id);
    ###
    # Attach edge
    ###
    nodeOne.edgeIds.append(edge.id);
    nodeTwo.edgeIds.append(edge.id);
    ###
    # Calculate length
    ###
    index = edge.nodeIds.index(nodeOne.id);
    jndex = edge.nodeIds.index(nodeTwo.id);
    if index > jndex:
        index, jndex = jndex, index;
    nodeIds = [nodeId for nodeId in edge.nodeIds[index : jndex + 1] if nodeId in id2Node];
    assert(len(nodeIds));
    length = sum(id2Node.get(nodeIds[index + 1]) - id2Node.get(nodeIds[index]) for index in range(len(nodeIds) - 1));
    ###
    # Attach it
    ###
    nodeOne.lengths.append(length);
    nodeTwo.lengths.append(length);
    ###
    return;

def BuildGraph(id2Node, id2Edge):
    PrintNow('Building graph ... ', end = '');
    intersectionIds = set();
    for edge in id2Edge.values():
        intersections = [];
        for nodeId in edge.nodeIds:
            node = id2Node.get(nodeId);
            ###
            if node is not None and len(node) > 1:
                intersections.append(node);
                intersectionIds.update((nodeId, ));
        ###
        prev = None;
        for curr in intersections:
            if prev is not None and prev.id != curr.id:
                LinkNodes(prev, curr, edge, id2Node);
            prev = curr;
    intersectionIds = list(intersectionIds);
    PrintNow('found {:d} intersections'.format(len(intersectionIds)));
    ###
    return intersectionIds;

def FloodFill(startId, id2Node, label):
    '''http://en.wikipedia.org/wiki/Flood_fill''';
    ###
    # Initialize
    ###
    count = 0;
    node = id2Node.get(startId);
    ###
    # If this node is unlabeled ...
    ###
    if node.label is None:
        ###
        # ... count it ...
        ###
        node.label = label;
        count += 1;
        ###
        for nodeId in node.nodeIds:
            ###
            # ... and recurse
            ###
            count += FloodFill(nodeId, id2Node, label);
    ###
    return count;

def TrimGraph(id2Node):
    PrintNow('Finding largest subgraph ... ', end = '');
    ###
    label2Count = {};
    label = 0;
    for nodeId in id2Node:
        count = FloodFill(nodeId, id2Node, label);
        if count:
            label2Count[label] = count;
            ###
            count = 0;
            label += 1;
    ###
    graphLabel = maxCount = 0;
    for label, count in label2Count.items():
        if count >= maxCount:
            graphLabel, maxCount = label, count;
    ###
    graphIds = {nodeId : node for nodeId, node in id2Node.items() if node.label == graphLabel};
    PrintNow('contains {:d} nodes'.format(len(graphIds)));
    ###
    return graphIds;

def SimpleDistance(latitude1, longitude1, latitude2, longitude2):
    return ((meterPerLat * (latitude1 - latitude2)) ** 2 + (meterPerLng * (longitude1 - longitude2)) ** 2);

def FakeLink(nodeIds, id2Node, id2Edge):
    ###
    # Find unique edgeId
    ###
    edgeId = max(id2Edge);
    ###
    # Iterate over every pairing
    ###
    for index in range(len(nodeIds)):
        nodeId = nodeIds[index];
        iNode = id2Node.get(nodeId);
        ###
        for jndex in range(index + 1, len(nodeIds)):
            nodeJd = nodeIds[jndex];
            jNode = id2Node.get(nodeJd);
            ###
            # Attach nodes
            ###
            iNode.nodeIds.append(nodeJd);
            jNode.nodeIds.append(nodeId);
            ###
            # Create fake edge and attach it
            ###
            edgeId += 1;
            id2Edge[edgeId] = Edge(False, edgeId, 'Edge to close graph between {:d} and {:d}'.format(nodeId, nodeJd), [nodeId, nodeJd], 0);
            ###
            iNode.edgeIds.append(edgeId);
            jNode.edgeIds.append(edgeId);
            ###
            # Attach length
            ###
            iNode.lengths.append(0);
            jNode.lengths.append(0);
    ###
    return;

def CloseGraph(id2Node, id2Edge, graphIds):
    PrintNow('Closing graph ... ', end = '');
    ###
    # Order nodes by position
    ###
    graphIds = sorted(graphIds, key = lambda graphId: (id2Node.get(graphId).latitude, id2Node.get(graphId).longitude));
    ###
    # Iterate over graph nodes
    ###
    threshold = 5;
    latlng2NodeIds = {};
    for nodeId in graphIds:
        node = id2Node.get(nodeId);
        latitude, longitude = node.latitude, node.longitude;
        match = False;
        for latlng in latlng2NodeIds:
            if SimpleDistance(latlng[0], latlng[1], latitude, longitude) < threshold:
                match = True;
                break;
        ###
        if match:
            latlng2NodeIds[latlng].append(node.id);
        else:
            latlng2NodeIds[(latitude, longitude)] = [node.id];
    ###
    count = 0;
    for latlng, nodeIds in latlng2NodeIds.items():
        if len(nodeIds) > 1:
            count += 1;
            FakeLink(nodeIds, id2Node, id2Edge);
    ###
    PrintNow('closed {:d} disconnections.'.format(count));
    ###
    return;

def NearestNode(latitude, longitude, nodeIds, id2Node):
    minimumId, minimumDistance = None, 1e9;
    for nodeId in nodeIds:
        node = id2Node.get(nodeId);
        distance = SimpleDistance(latitude, longitude, node.latitude, node.longitude);
        if distance < minimumDistance:
            minimumId, minimumDistance = nodeId, distance;
    ###
    return minimumId, minimumDistance ** 0.5;

def SnapPOIs(id2Node, nodeIds, datDirectory):
    ###
    # Grab dog-friendly POI's
    ###
    dogOKFileName = '{}/dogOKs.dat'.format(datDirectory);
    with open(dogOKFileName) as f:
        dogOKs = [dogOK.strip() for dogOK in f.readlines()];
    ###
    # Iterate over POI types
    ###
    id2Poi = {};
    for poiType in poiTypes:
        PrintNow('Snapping {} to intersections ...'.format(poiType));
        ###
        # POI specifics
        ###
        skip = poiType2Skip.get(poiType);
        ###
        # Read POI .json
        ###
        jsonFileName = '{}/{}.json'.format(datDirectory, poiType);
        PrintNow('Reading {:s} ... '.format(jsonFileName), end = '');
        with open(jsonFileName, 'r') as f:
            json = JSONLoad(f.read());
        PrintNow('done');
        ###
        # Iterate over businesses
        ###
        businesses = json.get('businesses');
        length = len(businesses);
        ###
        for index in range(length):
            ###
            # Skip junk data and dog-unfriendly
            ###
            yelpUrl = businesses[index].get('url');
            if index in skip or yelpUrl not in dogOKs:
                continue;
            ###
            json = businesses[index];
            ###
            poiId = POIHash(json, poiType);
            latlng = json.get('location').get('latlng');
            ###
            # Kick out ill-defined POI's
            ###
            if latlng is None:
                continue;
            ###
            # Attach ...
            ###
            PrintNow('{:4d}/{:4d}:\t{} .. '.format(index + 1, length, json.get('name')), end = '');
            ###
            latitude, longitude = latlng;
            nodeId, offset = NearestNode(latitude, longitude, nodeIds, id2Node);
            ###
            PrintNow('to {}'.format(nodeId));
            ###
            # ... POI onto node ...
            ###
            id2Node.get(nodeId).poiIds.append(poiId);
            ###
            # ... and node onto POI
            ###
            if poiId in id2Poi:
                id2Poi.get(poiId).nodeIds.append(nodeId);
                id2Poi.get(poiId).offsets.append(offset);
            else:
                id2Poi[poiId] = POI(json, poiType, [nodeId], [offset]);
    ###
    PrintNow('Added {:d} POIs'.format(len(id2Poi)));
    ###
    return id2Poi;

def SnapTrees(id2Node, id2Edge, graphIds, datDirectory):
    id2Tree = {};
    PrintNow('Snapping trees to edges ...');
    ###
    # Map nodeId to edgeIds
    ###
    nodeId2EdgeIds = {};
    for edgeId, edge in id2Edge.items():
        ###
        # Kick out non-subgraph edges
        ###
        if not any(nodeId in graphIds for nodeId in edge.nodeIds):
            continue;
        ###
        for nodeId in edge.nodeIds:
            ###
            # Kick out missing nodes
            ###
            if nodeId not in id2Node:
                continue;
            ###
            try:
                nodeId2EdgeIds[nodeId].append(edgeId);
            except KeyError:
                nodeId2EdgeIds[nodeId] = [edgeId];
    ###
    # Order nodes by position
    ###
    nodeIds = sorted(nodeId2EdgeIds.keys(), key = lambda nodeId: (id2Node.get(nodeId).latitude, id2Node.get(nodeId).longitude));
    ###
    # Read tree .json
    ###
    jsonFileName = '{}/{}.json'.format(datDirectory, treeFileName);
    PrintNow('Reading {:s} ... '.format(jsonFileName), end = '');
    with open(jsonFileName, 'r') as f:
        json = JSONLoad(f.read());
    PrintNow('done');
    ###
    # Iterate over trees
    ###
    trees = json.get('data');
    ###
    # Order trees by position
    ###
    trees = sorted((tree for tree in trees if tree[23] is not None and tree[24] is not None), key = lambda tree: (tree[23], tree[24]));
    ###
    length = len(trees);
    prevLatLng, prevNodeId = (None, None), None;
    for index in range(length):
        treeList = trees[index];
        ###
        treeId = treeList[0];
        variety = treeList[10];
        latitude, longitude = treeList[23 : 25];
        ###
        # Kick out ill-defined or repeat trees
        ###
        if latitude is None or longitude is None:
            continue;
        ###
        # Snap to a node ...
        ###
        PrintNow('{:5d}/{:5d} .. '.format(index + 1, length, treeList[10][ : 10]), end = '');
        ###
        id2Tree[treeId] = Tree(treeId, variety, latitude, longitude);
        latitude, longitude = float(latitude), float(longitude);
        if prevLatLng == (latitude, longitude):
            nodeId = prevNodeId;
        else:
            nodeId, junk = NearestNode(latitude, longitude, nodeIds, id2Node);
            ###
            prevLatLng, prevNodeId = (latitude, longitude), nodeId;
        ###
        # ... grab its edges ...
        ###
        edgeIds = nodeId2EdgeIds.get(nodeId);
        ###
        # ... and increment them
        ###
        PrintNow('to {}'.format(','.join(str(edgeId) for edgeId in edgeIds)));
        for edgeId in edgeIds:
            id2Edge.get(edgeId).treeCount += 1;
    ###
    PrintNow('Added {:d} trees'.format(len(id2Tree)));
    ###
    return id2Tree;

def CreateTables(id2Node, id2Edge, id2Poi, id2Tree, graphIds):
    ###
    # Helper
    ###
    def List2Str(l):
        return l and ','.join(str(e) for e in l if e) or '';
    ###
    # Initialize
    ###
    connection = MySqlConnect(user = 'root', port = 3306, db = mySqlDataBase);
    cursor = connection.cursor();
    ###
    # Nodes
    ###
    PrintNow('Nodes TABLE ... ', end = '');
    cursor.execute('''DROP TABLE Nodes ;''');
    cursor.execute('''CREATE TABLE Nodes (id INT UNSIGNED NOT NULL PRIMARY KEY, isIntersection BOOLEAN, latitude DOUBLE NOT NULL, longitude DOUBLE NOT NULL, nodeIds TINYBLOB, edgeIds TINYBLOB, lengths TINYBLOB, poiIds TINYBLOB) ;''');
    for node in id2Node.values():
        cursor.execute('''INSERT INTO Nodes(id, isIntersection, latitude, longitude, nodeIds, edgeIds, lengths, poiIds) VALUES ({0.id:d}, {1:d}, {0.latitude:f}, {0.longitude:f}, "{2:s}", "{3:s}", "{4:s}", "{5:s}") ;'''.format(node, bool(node.id in graphIds), List2Str(node.nodeIds), List2Str(node.edgeIds), List2Str(node.lengths), List2Str(node.poiIds)));
    connection.commit();
    PrintNow('inserted {:d} rows'.format(len(id2Node)));
    ###
    # Edges
    ###
    PrintNow('Edges TABLE ... ', end = '');
    cursor.execute('''DROP TABLE Edges ;''');
    cursor.execute('''CREATE TABLE Edges (id INT UNSIGNED NOT NULL PRIMARY KEY, name TINYBLOB NOT NULL, nodeIds TINYBLOB NOT NULL, treeCount INT UNSIGNED NOT NULL) ;''')
    for edge in id2Edge.values():
        cursor.execute('''INSERT INTO Edges(id, name, nodeIds, treeCount) VALUES ({0.id:d}, "{1:s}", "{2:s}", {0.treeCount:d}) ;'''.format(edge, edge.name, List2Str(edge.nodeIds)));
    connection.commit();
    PrintNow('inserted {:d} rows'.format(len(id2Edge)));
    ###
    # POIs
    ###
    PrintNow('POIs TABLE ... ', end = '');
    cursor.execute('''DROP TABLE POIs ;''');
    cursor.execute('''CREATE TABLE POIs (id BIGINT NOT NULL PRIMARY KEY, poiType TINYBLOB NOT NULL, name TINYBLOB NOT NULL, nodeIds TINYBLOB NOT NULL, offsets TINYBLOB NOT NULL, latitude DOUBLE NOT NULL, longitude DOUBLE NOT NULL, address TINYBLOB NOT NULL, city TINYBLOB NOT NULL, state TINYBLOB NOT NULL, imageUrl TINYBLOB NOT NULL, yelpUrl TINYBLOB NOT NULL) ;''');
    count = 0;
    for poi in id2Poi.values():
        if (poi.latitude is None or poi.longitude is None):
            continue;
        ###
        count += 1;
        cursor.execute('''INSERT INTO POIs(id, poiType, name, nodeIds, offsets, latitude, longitude, address, city, state, imageUrl, yelpUrl) VALUES ({0.id:d}, "{0.poiType:s}", "{1:s}", "{2:s}", "{3:s}", {0.latitude:f}, {0.longitude:f}, "{4:s}", "{0.city:s}", "{0.state:s}", "{0.imageUrl:s}", "{0.yelpUrl:s}") ;'''.format(poi, poi.name, List2Str(poi.nodeIds), List2Str(poi.offsets), poi.address[0]));
    ###
    connection.commit();
    PrintNow('inserted {:d} rows'.format(count));
    ###
    # Trees
    ###
    PrintNow('Trees TABLE .. ', end = '');
    cursor.execute('''DROP TABLE Trees ;''');
    cursor.execute('''CREATE TABLE Trees (id INT UNSIGNED NOT NULL PRIMARY KEY, variety TINYBLOB NOT NULL, latitude DOUBLE NOT NULL, longitude DOUBLE NOT NULL) ;''');
    count = 0;
    for tree in id2Tree.values():
        if (tree.latitude is None or tree.longitude is None):
            continue;
        ###
        count += 1;
        cursor.execute('''INSERT INTO Trees(id, variety, latitude, longitude) VALUES ({0.id:d}, "{0.variety:s}", {0.latitude:f}, {0.longitude:f}) ;'''.format(tree));
    ###
    connection.commit();
    PrintNow('inserted {:d} rows'.format(count));
    ###
    # Debug
    ###
    if False:
        cursor.execute('''SELECT * FROM POIs ;''');
        PrintNow(*('\t'.join(str(col) for col in row) for row in cursor), sep = '\n');
    ###
    # Garbage
    ###
    connection.close();
    ###
    return;

def Mashup(osmFileName, datDirectory, pickleFileName = None):
    ###
    # Maybe load pickle
    ###
    pickleFileName = '{}/{}'.format(datDirectory, pickleFileName);
    if Exists(pickleFileName):
        PrintNow('Reading {:s} ... '.format(pickleFileName), end = '');
        ###
        # Load pickle
        ###
        with open(pickleFileName, 'rb') as f:
            pickle = UnPickle(f);
        ###
        id2Node = pickle.get('id2Node');
        id2Edge = pickle.get('id2Edge');
        intersectionIds = pickle.get('intersectionIds');
        graphIds = pickle.get('intersectionIds');
        id2Poi = pickle.get('id2Poi');
        id2Tree = pickle.get('id2Tree');
        ###
        PrintNow('done');
    else:
        PrintNow('Pickle `{}` was not found ... generating graph instead'.format(pickleFileName));
        ###
        # Read OSM file
        ###
        osmFileName = '{}/{}'.format(datDirectory, osmFileName);
        osmRoot = ReadOsmFile(osmFileName);
        ###
        # Parse OSM nodes
        ###
        id2Node = ParseOSMNodes(osmRoot);
        ###
        # Parse OSM ways
        ###
        id2Edge = ParseOSMWays(osmRoot, id2Node);
        ###
        # Build graph
        ###
        intersectionIds = BuildGraph(id2Node, id2Edge);
        ###
        # Trim disconnected graphs
        ###
        graphIds = TrimGraph(id2Node);
        ###
        # Link identical nodes with 0-length edges
        ###
        CloseGraph(id2Node, id2Edge, graphIds);
        ###
        # Snap POI's to intersection nodes
        ###
        id2Poi = SnapPOIs(id2Node, graphIds, datDirectory);
        ###
        # Snap Trees to edges
        ###
        id2Tree = SnapTrees(id2Node, id2Edge, graphIds, datDirectory);
        ###
        # Dump pickle
        ###
        dat = {
            'id2Node' : id2Node,
            'id2Edge' : id2Edge,
            'intersectionIds' : intersectionIds,
            'graphIds' : graphIds,
            'id2Poi' : id2Poi,
            'id2Tree' : id2Tree,
        };
        ###
        with open(pickleFileName, 'wb') as f:
            PrintNow('Writing {:s} ... '.format(pickleFileName), end = '');
            Pickle(dat, f);
            PrintNow('done');
    ###
    # Write MySql tables
    ###
    CreateTables(id2Node, id2Edge, id2Poi, id2Tree, graphIds);
    ###
    return;

###
### Post MySQL
###

def MySql2Graph():
    ###
    # Connect to database and initialize cursor
    ###
    PrintNow('Using {} ... '.format(mySqlDataBase), end = '');
    connection = MySqlConnect(user = 'root', port = 3306, db = mySqlDataBase);
    cursor = connection.cursor();
    PrintNow('done');
    ###
    # id2Node
    ###
    PrintNow('Loading Nodes ... ', end = '');
    cursor.execute('''SELECT * FROM Nodes ;''');
    id2Node = {nodeId : Node(nodeId, *other) for nodeId, *other in cursor};
    PrintNow('found {:d}'.format(len(id2Node)));
    ###
    # id2Edge
    ###
    PrintNow('Loading Edges ... ', end = '');
    cursor.execute('''SELECT * FROM Edges ;''');
    id2Edge = {edgeId : Edge(edgeId, *other) for edgeId, *other in cursor};
    PrintNow('found {:d}'.format(len(id2Edge)));
    ###
    # id2Poi
    ###
    PrintNow('Loading POIs ... ', end = '');
    cursor.execute('''SELECT * FROM POIs ;''');
    id2Poi = {poiId : POI(poiId, *other) for poiId, *other in cursor};
    PrintNow('found {:d}'.format(len(id2Poi)));
    ###
    # id2Tree
    ###
    PrintNow('Loading Trees ... ', end = '');
    cursor.execute('''SELECT * FROM Trees ;''');
    id2Tree = {treeId : Tree(False, treeId, *other) for treeId, *other in cursor};
    PrintNow('found {:d}'.format(len(id2Tree)));
    ###
    # graphIds
    ###
    graphIds = list(nodeId for nodeId, node in id2Node.items() if node.isIntersection);
    ###
    PrintNow('Finished loading MySQL database `{}`.'.format(mySqlDataBase));
    ###
    return id2Node, id2Edge, id2Poi, id2Tree, graphIds;

def FindPOIs(nodeIds, id2Node, id2Poi):
    PrintNow('Locating POI\'s ... ', end = '');
    poiIds = list(set(poiId for nodeId in nodeIds for poiId in id2Node.get(nodeId).poiIds if poiId in id2Poi));
    PrintNow('found {:d}'.format(len(poiIds)));
    return poiIds;

def LatLngDistance(latitude1, longitude1, latitude2, longitude2):
    '''http://www.johndcook.com/python_longitude_latitude.html''';
    ###
    phi1 = (90 - latitude1) * radiansPerDegree;
    phi2 = (90 - latitude2) * radiansPerDegree;
    ###
    deltaTheta = (longitude1 - longitude2) * radiansPerDegree;
    ###
    argument = Sine(phi1) * Sine(phi2) * Cosine(deltaTheta) + Cosine(phi1) * Cosine(phi2);
    ###
    # Positions are the same!
    ###
    if argument > 1:
        return 0;
    ###
    return radiusOfEarth * ArcCosine(argument);

def ExtremeNode(nodeIds, id2Node, attribute, index):
    return list(sorted((getattr(node, attribute), nodeId) for nodeId in nodeIds for node in [id2Node.get(nodeId)]))[index][1];

def BottomNode(nodeIds, id2Node):
    return ExtremeNode(nodeIds, id2Node, attribute = 'latitude', index = -1);

def LeftNode(nodeIds, id2Node):
    return ExtremeNode(nodeIds, id2Node, attribute = 'longitude', index = 0);

def RightNode(nodeIds, id2Node):
    return ExtremeNode(nodeIds, id2Node, attribute = 'longitude', index = -1);

def TopNode(nodeIds, id2Node):
    return ExtremeNode(nodeIds, id2Node, attribute = 'latitude', index = 0);

def CropGraph(center, radius, id2Thing, thingIds, description):
    PrintNow('Cropping {:G}km around ({:G}, {:G}) ... '.format(radius / 1e3, *center), end = '');
    ###
    # Crop to square
    ###
    xmin, xmax, ymin, ymax = center[1] - radius / meterPerLng, center[1] + radius / meterPerLng, center[0] - radius / meterPerLat, center[0] + radius / meterPerLat;
    things = [thing for thingId in thingIds for thing in [id2Thing.get(thingId)] if xmin <= thing.longitude <= xmax and ymin <= thing.latitude <= ymax];
    ###
    # Crop to circle
    ###
    croppedIds = [thing.id for thing in things if LatLngDistance(center[0], center[1], thing.latitude, thing.longitude) <= radius];
    ###
    PrintNow('{:d} {:s} remain'.format(len(croppedIds), description));
    ###
    return croppedIds;

def GeoCode(address):
    from urllib.request import urlopen as UrlOpen;
    from urllib.parse import quote as Quote;
    ###
    # Encode query string into URL
    ###
    url = 'http://maps.googleapis.com/maps/api/geocode/json?address={}&sensor=false'.format(Quote(address));
    ###
    # Call API and extract JSON
    ###
    PrintNow('Calling Google Maps API for `{:s}` ... '.format(address), end = '');
    json = UrlOpen(url).read();
    json = JSONLoad(json.decode('utf-8'));
    ###
    # Extract longitude and latitude
    ###
    if json.get('status') == 'ZERO_RESULTS':
        latitude, longitude = None, None;
        ###
        PrintNow('it was not found');
    else:
        latitude, longitude = (value for key, value in sorted(json.get('results')[0].get('geometry').get('location').items()));
        ###
        PrintNow('it is located at {:f}/{:f}'.format(latitude, longitude));
    ###
    return Address(address, latitude, longitude);

def FindAddress(query, minutes, id2Node, id2Poi, graphIds, id2Tree):
    ###
    # Specify San Francisco!
    ###
    if all(city not in query.lower() for city in ('sf', 'san francisco', 's.f.')):
        query += ', San Francisco, CA';
    ###
    # Geocode it
    ###
    address = GeoCode(query);
    ###
    # Check if the address is in bounds
    ###
    if address.latitude is None or address.longitude is None or not InBounds(address):
        return None;
    ###
    # Grab address lat/lng
    ###
    latlng = (address.latitude, address.longitude);
    ###
    # Calculate center, radius, and bounds
    ###
    center = (address.latitude, address.longitude);
    radius = meterPerMin * minutes;
    ###
    bounds = [[center[0] - radius / meterPerLat, center[1] - radius / meterPerLng], [center[0] + radius / meterPerLat, center[1] + radius / meterPerLng]];
    ###
    # Crop graph
    ###
    bufferIds = CropGraph(center, radius * 2.5, id2Node, graphIds, 'nodes');
    croppedIds = CropGraph(center, radius, id2Node, bufferIds, 'nodes');
    ###
    # Snap to nearest node
    ###
    nodeId, offset = NearestNode(address.latitude, address.longitude, croppedIds, id2Node);
    ###
    # Find POI's
    ###
    poiIds = FindPOIs(croppedIds, id2Node, id2Poi);
    POIs = [id2Poi.get(poiId) for poiId in poiIds];
    ###
    # Find trees
    ###
    trees = [id2Tree.get(treeId) for treeId in CropGraph(center, radius * 1.5, id2Tree, id2Tree, 'trees')];
    ###
    # Build JSON
    ###
    json = {
        'query' : query,
        'minutes' : minutes,
        'address' : GeoJSON(address),
        'addressLatlng' : latlng,
        'center' : center,
        'radius' : radius,
        'bounds' : bounds,
        'croppedIds' : bufferIds,
        'nodeId' : nodeId,
        'offset' : offset,
        'poiIds' : poiIds,
        'POIs' : GeoJSON(POIs),
        'trees' : GeoJSON(trees),
    };
    ###
    return json;

def FinePath(pathIds, nodeIds, id2Node, id2Edge):
    PrintNow('Building fine path ... ', end = '');
    ###
    # Build path points
    ###
    longitudes, latitudes = [], [];
    previous = current = None;
    ###
    for nodeId in pathIds:
        current = id2Node.get(nodeId);
        ###
        if previous is not None:
            edgeId = current.edgeIds[current.nodeIds.index(previous.id)];
            edge = id2Edge.get(edgeId);
            ###
            index = edge.nodeIds.index(previous.id);
            jndex = edge.nodeIds.index(current.id);
            ###
            if index > jndex:
                step = -1;
            else:
                step = +1;
            nodeIds = edge.nodeIds[index : jndex + step : step];
            ###
            longitudes.extend((id2Node.get(nodeId).longitude for nodeId in nodeIds));
            latitudes.extend((id2Node.get(nodeId).latitude for nodeId in nodeIds));
        ###
        previous = current;
    latlngs = list(zip(latitudes, longitudes));
    ###
    PrintNow('contains {:d} fine nodes'.format(len(longitudes)));
    ###
    return latlngs;

def Dijkstra(start, finishes, id2Node, id2Edge):
    assert(start in id2Node);
    assert(all(finish in id2Node for finish in finishes));
    ###
    # Initialize
    ###
    uninspected = id2Node.copy();
    ###
    id2Distance = {nodeId : 1e9 for nodeId in uninspected};
    id2Distance[start] = 0;
    id2From = {};
    ###
    # Inspect each node
    ###
    while uninspected:
        ###
        # Walk to nearest node
        ###
        distance = min(id2Distance.get(nodeId) for nodeId in uninspected);
        nearest = next(nodeId for nodeId in uninspected if distance == id2Distance.get(nodeId));
        ###
        # Kick out if at finish
        ###
        if nearest in finishes:
            break;
        ###
        # Declare nearest to be inspected
        ###
        nearest = uninspected.pop(nearest);
        ###
        # Walk to each uninspected neighbor
        ###
        for nodeId, edgeId, length in zip(nearest.nodeIds, nearest.edgeIds, nearest.lengths):
            ###
            # Kick out inspected
            ###
            if nodeId not in uninspected:
                continue;
            ###
            # Reduce edge distance according to tree density
            ###
            edge = id2Edge.get(edgeId);
            treePerMeter = distance and edge.treeCount / distance;
            distance *= (1 - min(maximumDistanceReduction, treePerMeter / maximumTreePerMeter));
            ###
            # Calculate distance
            ###
            length += distance;
            ###
            # Use shortest path
            ###
            if length < id2Distance.get(nodeId):
                id2Distance[nodeId] = length;
                id2From[nodeId] = nearest.id;
    ###
    # Construct shortest path
    ###
    nodeId = nearest;
    path = [nodeId];
    while nodeId != start:
        nodeId = id2From.get(nodeId);
        path.insert(0, nodeId);
    ###
    return path, id2Distance.get(nearest);

def Route(startId, finishIds, nodeIds, id2Node, id2Edge):
    PrintNow('Routing a path from {:d} to {:s} ... '.format(startId, finishIds), end = '');
    subGraph = {nodeId : id2Node.get(nodeId) for nodeId in nodeIds};
    pathIds, distance = Dijkstra(startId, finishIds, subGraph, id2Edge);
    PrintNow('{:d} edges take {:G}km'.format(len(pathIds) - 1, distance / 1e3));
    ###
    return pathIds, distance;

def RoutePOI(startId, poiId, nodeIds, id2Node, id2Edge, id2Poi):
    ###
    # Extract POI
    ###
    poi = id2Poi.get(poiId);
    finishIds = poi.nodeIds;
    ###
    # Route
    ###
    pathIds, distance = Route(startId, finishIds, nodeIds, id2Node, id2Edge);
    ###
    # Build fine-path
    ###
    latlngs = FinePath(pathIds, nodeIds, id2Node, id2Edge);
    ###
    # Grab offset
    ###
    offset = poi.offsets[poi.nodeIds.index(pathIds[-1])];
    ###
    # Build JSON
    ###
    json = {
        'startId' : startId,
        'poiId' : poiId,
        'finishIds' : finishIds,
        'poiType' : poi.poiType,
        'poiName' : poi.name,
        'poiLatlng' : (poi.latitude, poi.longitude),
        'offset' : offset,
        'pathIds' : pathIds,
        'distance' : distance,
        'latlngs' : latlngs,
    };
    ###
    return json;

def DebugPlot(pathIds, nodeIds, id2Node, id2Edge, pdfFileName = 'debug.pdf'):
    import matplotlib.pyplot as Plot;
    ###
    PrintNow('Plotting graph ... ', end = '');
    ###
    # Initialize
    ###
    fig, ax = Plot.subplots();
    ###
    # Draw Streets
    ###
    x, y = [], [];
    ###
    for nodeId in nodeIds:
        iNode = id2Node.get(nodeId);
        ###
        for nodeJd in iNode.nodeIds:
            edge = id2Edge.get(iNode.edgeIds[iNode.nodeIds.index(nodeJd)]);
            ###
            index = edge.nodeIds.index(nodeId);
            jndex = edge.nodeIds.index(nodeJd);
            ###
            if index > jndex:
                step = -1;
            else:
                step = +1;
            nodeIds = edge.nodeIds[index : jndex + step : step];
            ###
            x.extend((id2Node.get(nodeId).longitude for nodeId in nodeIds));
            y.extend((id2Node.get(nodeId).latitude for nodeId in nodeIds));
            ###
            x.append(None);
            y.append(None);
    ###
    Plot.plot(x, y, color = 'black', linewidth = 0.5);
    ###
    # Draw Intersections
    ###
    x, y = [], [];
    for nodeId in nodeIds:
        node = id2Node.get(nodeId);
        x.extend((node.longitude, None));
        y.extend((node.latitude, None));
    Plot.plot(x, y, marker = 'o', markersize = 1, markerfacecolor = 'blue', markeredgecolor = 'blue');
    ###
    # Draw path
    ###
    x, y = [], [];
    previous = current = None;
    ###
    for nodeId in pathIds:
        current = id2Node.get(nodeId);
        ###
        if previous is not None:
            edge = id2Edge.get(current.edgeIds[current.nodeIds.index(previous.id)]);
            ###
            index = edge.nodeIds.index(previous.id);
            jndex = edge.nodeIds.index(current.id);
            ###
            if index > jndex:
                step = -1;
            else:
                step = +1;
            nodeIds = edge.nodeIds[index : jndex + step : step];
            ###
            x.extend((id2Node.get(nodeId).longitude for nodeId in nodeIds));
            y.extend((id2Node.get(nodeId).latitude for nodeId in nodeIds));
            ###
            x.append(None);
            y.append(None);
        ###
        previous = current;
    ###
    Plot.plot(x, y, color = 'orange', linewidth = 4, alpha = 0.5, marker = None);
    ###
    # Draw start/finish
    ###
    startId, finishId = pathIds[0], pathIds[-1];
    x, y = id2Node.get(startId).longitude, id2Node.get(startId).latitude;
    Plot.plot(x, y, marker = 'x', markersize = 8, markeredgewidth = 2, markerfacecolor = 'green', markeredgecolor = 'green');
    ###
    x, y = id2Node.get(finishId).longitude, id2Node.get(finishId).latitude;
    Plot.plot(x, y, marker = 'x', markersize = 8, markeredgewidth = 2, markerfacecolor = 'green', markeredgecolor = 'red');
    ###
    # Pretty
    ###
    ax.set_xlim((-122.4592000, -122.4156000));
    ax.set_ylim((37.7719000, 37.7923000));
    ax.set_title('Path from {:d} to {:d}'.format(startId, finishId))
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    fig.savefig(pdfFileName);
    ###
    PrintNow('saved to {:d}'.format(pdfFileName));
    ###
    return;

###
### Filenames
###

datDirectory = './static/dat' ;
###
osmFileName = 'neighborhood.osm' ;
osmFileName = 'sf-city.osm' ;
###
treeFileName = 'sfTrees';
###
mySqlDataBase = 'dogWalkScore5';
###
pickleFileName = '{}.pkl'.format(mySqlDataBase);

###
### Script
###

if __name__ == '__main__':
    Mashup(osmFileName, datDirectory, pickleFileName);
