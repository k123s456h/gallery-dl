apk add iptables
iptables -A INPUT -p tcp --tcp-flags RST RST --sport 443 -j DROP