# CLAUDE.md — Project hints for AI assistants

## Project

This folder contains a zephyr application which runs on a Raspberry Pi Pico.

The program is already implemented in micropython, see "./main.py".
This program should now be rewritten in C/C++ to run on zephyr.

## Zephyr

- Build the code in this directory using heatguard_zephyr/.devcontainer/devcontainer.json

## Required Results

* Directorystructure as used for a common zephyr application.
* Script which compiles the sources into the firmware using ghcr.io/zephyrproject-rtos/zephyr-build:main.
