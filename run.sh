#!/bin/bash

if [ "$USER" == "root" ]; then
	cd /home/sdn
	source venv/bin/activate
	cd AmbienteVirtualMininet
	mkdir -p relatorios
	python3 main.py
	rm -f controller_routing_mode.tmp graph_topo.pickle
	chown sdn:sdn relatorios/*
else
	sudo $0
fi
