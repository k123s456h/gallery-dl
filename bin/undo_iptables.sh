#!/bin/sh

iptables -D INPUT -p tcp --tcp-flags RST RST --sport 443 -j DROP