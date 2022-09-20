#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
PYTHONPATH := `pwd`


#* Installation
.PHONY: install
install:
	# create $HOME/.cdsapirc file
	# install poetry
