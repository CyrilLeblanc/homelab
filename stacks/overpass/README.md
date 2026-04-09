# Overpass 

## Setup

```sh

# start the stack. It will crash but it's normal we need to generate a planet.osm.bz2
#  download the pbf in /data inside the container :
curl -L http://download.geofabrik.de/europe/france/rhone-alpes-latest.osm.pbf -o /var/lib/docker/volumes/osmium_data/_data/planet.osm.pbf

# overpass need a bz2 file so we use the osmium inside the container to do that
osmium cat /var/lib/docker/volumes/osmium_data/_data/planet.osm.pbf -o /var/lib/docker/volumes/osmium_data/_data/planet.osm.bz2 --overwrite

# now you need to set the `OVERPASS_MODE` to "init" and start the stack.
# It will index everything in the .bz2 file. The container will stop once this is done but it take a lot of time (30-40m)
# Then you can change the value of `OVERPASS_MODE` to "clone" and it will ready to use.

# > This setup doesn't include auto update yet.
```