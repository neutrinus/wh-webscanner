{% load l10n %}

<p>We use GeoIP database to estimate geolocation of your servers, please note that locations are approximated.</p>
<div id="{{ id }}" style="height:250px"></div>

{% localize off %}

<script>
    map = new OpenLayers.Map("{{ id }}");
    map.addLayer(new OpenLayers.Layer.OSM());
    var markers = new OpenLayers.Layer.Markers( "Markers" );
    map.addLayer(markers);
    
    
    {% for address, in_dict in locations.items %}
        var marker_{{ forloop.counter }} = new OpenLayers.LonLat({{ in_dict.longitude }},{{ in_dict.latitude }})
        .transform(
            new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
                   map.getProjectionObject() // to Spherical Mercator Projection
        );
        markers.addMarker(new OpenLayers.Marker(marker_{{ forloop.counter }}));
    {% endfor %}
    
    map.setCenter ([0,0], 1);
</script>

<ul>
{% for address, in_dict in locations.items %}
<li><b>{{ address }}</b> is located in {% if in_dict.city %}{{ in_dict.city }}, {% endif %}{{ in_dict.country_name }}</li>
{% endfor %}
</ul>    

{% endlocalize %}

 