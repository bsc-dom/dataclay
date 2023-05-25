#!/bin/bash

# Print the number of objects for each backend

objects=""
for key in $(redis-cli keys /object\*); do
	objects+="$(redis-cli GET $key)\n"
done

for key in $(redis-cli keys /backend* | awk -F "/" '{print $NF}'); do
	echo $key
	echo -e "$objects" | grep -c $key
done
