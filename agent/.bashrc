function get_errors { tail /sdc-data/errors/$1/$(ls -t /sdc-data/errors/$1 | head -1) | grep -oP '"errorMessage":.*?[^\\]",'; }

function get_destination_url { cat /usr/src/app/data/destination.json | grep -oP '"conf.resourceUrl":.*?[^\\]",'; }
