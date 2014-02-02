dogWalkScore
============

As WalkScore is to neighborhood walkability, dogWalkScore is to neighborhood dog-walkability.  dogWalkScore helps you find apartments in San Francisco which are near lots of dog-friendly bars and restaurants.  For each apartment, it provides a single score which accounts for the number and proximity of dog-friendly bars and restaurants.  The best walking routes to each one are also dynamically generated.

San Francisco street data (from `OpenStreetMap<http://www.openstreetmap.org>`_) was used to build a graph, onto which the locations of bars and restaurants (from `Yelp<http://www.yelp.com>`_) were attached.  The locations of 80,000 trees (from `SFData<https://data.sfgov.org/>`_) are also attached to the graph so that a modified Dijkstra algorithm can ensure plenty of dog-friendly trees along your route.
