CONTIKI ?= $(HOME)/contiki

TARGET = cooja
APPS = smart_sensor sink

CONTIKI_PROJECT = smart_sensor.c sink.c

include $(CONTIKI)/Makefile.include
