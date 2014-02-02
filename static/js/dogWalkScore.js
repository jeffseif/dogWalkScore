var addressQuery;
var bounds = [[37.708, -122.515], [37.8125, -122.355]];
var geoJSON = [];
var map;
var mapId = 'jeffreyseifried.h1n3d7d4' ;
var mapId = 'examples.map-20v6611k' ;
var poiPaths = [];
var poiMetrics = [];
var pathOptions = {color : 'red', opacity : 0.5, weight : 4};
var scoreColor;
var scoreDistance;
var scoreHi = 70.;
var scoreLo = 30.;
var scoreMax = 3;
var scoreMinutes2Distance = 15;
var scorePower = 0.5;
var scoreText;

function DogShit() {
    // ... reset map ...
    ResetMap();
    // ... and reset score ...
    ResetScore()
    // ... and hide loading
    ShowLoading(false);
};

function POISum(poiType, metrics) {
    // Sum POI's
    var total = 0;
    for (i = 0; i < metrics.length; i++) {
        if (poiType == metrics[i][0]) {
            total += Math.min(1, Math.pow(scoreDistance / metrics[i][1], scorePower));
        };
    };
    // Return
    return total;
};

function Score() {
    // Grab slider weights
    weightPark = parseFloat($('#play').val());
    weightPark = 0;
    weightBar = parseFloat($('#drink').val());
    weightRest = parseFloat($('#food').val());
    // Normalize them
    weightTotal = Math.max(1, weightPark + weightBar + weightRest);
    weightPark /= weightTotal;
    weightBar /= weightTotal;
    weightRest /= weightTotal;
    // Calculate score
    var score = weightPark * POISum('park', poiMetrics)
              + weightBar * POISum('bar', poiMetrics)
              + weightRest * POISum('restaurant', poiMetrics);
    // Normalize score
    score = Math.floor(Math.min(1, score / scoreMax) * 100);
    // Pick color
    switch(true) {
    case (score < scoreLo):
        color = 'salmon';
        break;
    case (score > scoreHi):
        color = 'limegreen';
        break;
    default:
        color = 'khaki'
        break;
    };
    // Set score text
    document.getElementById('score').innerText = 'Score: ' + score + ' / 100';
    // Set score color
    $('#score').css('background-color', color);
    // Show slider
    $('#slider').css('display', 'block');
    // Show score
    $('#score').css('display', 'block');
    // Hide loading
    ShowLoading(false);
};

function FindAndRoute(box) {
    // Grab address ...
    addressQuery = box;
    // ... show loading ...
    ShowLoading(true);
    // ... and grab minutes
    minutes = 7; // FIXME
    // Scale score distance with duration
    scoreDistance = minutes * scoreMinutes2Distance / 2;
    // Geocode it
    $.getJSON('/findAddress', {'q' : addressQuery, 'm' : minutes}, function(findJSON) {
        // Maybe reset on bad query
        if (findJSON != {}) {
            // Pan and zoom
            map.fitBounds(findJSON['bounds']);
            // Push address
            geoJSON.push(findJSON['address']);
            // Push POIs
            geoJSON = geoJSON.concat(findJSON['POIs']);
            // Draw geoJSON markers
            map.markerLayer.setGeoJSON(geoJSON);
            // Grab nodeIds
            nodeId = findJSON['nodeId'];
            poiIds = findJSON['poiIds'];
            // Route to each POI
            for (var j = 0; j < poiIds.length; j++) {
                $.getJSON('/routePOI', {'s' : nodeId, 'p' : poiIds[j]}, function(routeJSON) {
                    // Add address and POI to path
                    var latlngs = routeJSON['latlngs'];
                    latlngs.unshift(findJSON['addressLatlng']);
                    latlngs.push(routeJSON['poiLatlng']);
                    // Draw path
                    poiPaths.push(new L.polyline(latlngs, pathOptions).addTo(map));
                    // Populate score metrics
                    poiMetrics.push([routeJSON['poiType'], findJSON['offset'] + routeJSON['distance'] + routeJSON['offset']]);
                    // If we are at the last POI ...
                    if (j == poiMetrics.length) {
                        // ... push trees ...
                        geoJSON = geoJSON.concat(findJSON['trees']);
                        // ... and redraw geoJSON markers
                        map.markerLayer.setGeoJSON(geoJSON);
                        // ... score ...
                        Score();
                    };
                });
            };
            // Score if no POI's are found
            if (poiIds.length == 0) {
                // ... push trees ...
                geoJSON = geoJSON.concat(findJSON['trees']);
                // ... redraw geoJSON markers
                map.markerLayer.setGeoJSON(geoJSON);
                // ... and score
                Score();
            };
        } else {
            // FIXME Declare that it wasn't found
            // Hide loading
            ShowLoading(false);
        };
    });
};

function SliderMove() {
    // If a query exists ...
    if (addressQuery) {
        // ... update score
        Score();
    };
};

function ResetScore() {
    // Reset score text
    document.getElementById('score').innerText = scoreText;
    // Reset score color
    $('#score').css('background-color', scoreColor);
    // Hide score
    $('#score').css('display', 'none');
    // Hide slider
    $('#slider').css('display', 'none');
};

function ResetMap() {
    // Clear address query
    addressQuery = null;
    // Clear POI paths
    for (var i = poiPaths.length; i > 0; i--) {
        poiPaths.pop().setLatLngs([]).redraw();
    };
    // Clear POI metrics
    poiMetrics = [];
    // Clear address, tree, and POI markers
    geoJSON = [];
    map.markerLayer.setGeoJSON(geoJSON);
    // Reset pan and zoom
    map.fitBounds(bounds);
};

function PawClick() {
    // Grab address box value
    var box = $('#address').val();
    // Reset map ...
    ResetMap();
    // ... and reset score ...
    ResetScore()
    // If it is not empty ...
    if (box != '' && box != null) {
        // ... and find and route
        FindAndRoute(box);
    };
};

function KeyPress(event) {
    // Grab address box value
    var box = $('#address').val();
    // If it is empty ...
    if (box == '' || box == null) {
        // ... reset map ...
        ResetMap();
        // ... and reset score ...
        ResetScore()
    } else {
        // ... otherwise, if [enter] was pressed
        if (13 == event.keyCode) {
            // ... reset map ...
            ResetMap();
            // ... and reset score ...
            ResetScore()
            // ... and find and route
            FindAndRoute(box);
        };
    };
};

function ShowLoading(showLoading) {
    if (showLoading) {
        $('#loading').css('visibility', 'visible');
    } else {
        $('#loading').css('visibility', 'hidden');
    };
};

function Load() {
    // Grab default score color
    scoreColor = $('#menu').css('background-color');
    // Grab default score text
    scoreText = document.getElementById('score').innerText;
    // Initialize MapBox map
    map = L.mapbox.map('map', mapId, {zoomControl : false}).fitBounds(bounds);
    // Move zoom controls to top-right
    new L.Control.Zoom({position : 'topright'}).addTo(map);
    // Customize marker drawing
    map.markerLayer.on('layeradd', function(e) {
        var marker = e.layer,
            feature = marker.feature;
        //
        marker.setIcon(L.icon(feature.properties.icon));
        //
        if (feature.properties.yelpUrl != undefined) {
            var popup = '<a href="' + feature.properties.yelpUrl + '">' + 
                        feature.properties.title + '</a>';
            //
            marker.bindPopup(popup);
        };
    });
    // Debug
    if (false) {
        L.marker([37.74, -122.41], {icon:L.icon({iconSize : [48, 48], iconUrl : './static/img/bar-24.svg'})}).addTo(map);
        L.marker([37.74, -122.42], {icon:L.icon({iconSize : [48, 48], iconUrl : './static/img/circle-24.svg'})}).addTo(map);
        L.marker([37.74, -122.425], {icon:L.icon({iconSize : [48, 48], iconUrl : './static/img/circle-24.svg'})}).addTo(map);
        L.marker([37.74, -122.43], {icon:L.icon({iconSize : [48, 48], iconUrl : './static/img/park-24.svg'})}).addTo(map);
        L.marker([37.74, -122.44], {icon:L.icon({iconSize : [48, 48], iconUrl : './static/img/restaurant-24.svg'})}).addTo(map);
        L.marker([37.74, -122.45], {icon:L.icon({iconSize : [48, 48], iconUrl : './static/img/square-24.svg'})}).addTo(map);
        L.marker([37.74, -122.46], {icon:L.icon({iconSize : [48, 48], iconUrl : './static/img/star-24.svg'})}).addTo(map);
    };
};
