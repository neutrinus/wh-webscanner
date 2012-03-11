<p>We use GeoIP database to estimate geolocation of your servers, please note that locations are approximated.</p>
<div id="webserversmap" style="height:250px"></div>
<script>
    map = new OpenLayers.Map("webserversmap");
    map.addLayer(new OpenLayers.Layer.OSM());
    var markers = new OpenLayers.Layer.Markers( "Markers" );
    map.addLayer(markers);
    map.zoomToMaxExtent();
    
    
    var marker_1 = new OpenLayers.LonLat( -0.1279688 ,51.5077286 ).transform(
        new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
                                  map.getProjectionObject() // to Spherical Mercator Projection
        );   
    markers.addMarker(new OpenLayers.Marker(marker_1));
    
    
    map.setCenter([0,0], 1);
</script>


{% for location in locations %}
{{ location }}: {{ locations.location.latitude }} <br>
{% endfor %}