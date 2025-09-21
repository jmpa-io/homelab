#!/usr/bin/env bash

for ip in 192.168.0.158 192.168.0.146 192.168.0.180; do
    echo -n "$ip -> "
    dig +short @$ip grafana.jmpa.lab
done

