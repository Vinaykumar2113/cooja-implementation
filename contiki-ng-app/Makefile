# Makefile for Smart Environmental Monitoring and Energy-Efficient WSN Project
# Compatible with Contiki-NG and Contiki 2.7 / 3.0 / Cooja

CONTIKI_PROJECT = sink-node sensor-node
all: $(CONTIKI_PROJECT)

# Set Default Target if not provided (sky for TelosB / Tmote Sky, or cooja)
TARGET ?= sky

# Auto-detect CONTIKI path or default to standard installation paths
ifndef CONTIKI
  ifneq ($(wildcard ../contiki-ng),)
    CONTIKI = ../contiki-ng
  else ifneq ($(wildcard ../../contiki-ng),)
    CONTIKI = ../../contiki-ng
  else ifneq ($(wildcard /home/user/contiki-ng),)
    CONTIKI = /home/user/contiki-ng
  else ifneq ($(wildcard /home/user/contiki),)
    CONTIKI = /home/user/contiki
  else
    CONTIKI = ../..
  endif
endif

# Network and Routing Configuration
MAKE_ROUTING ?= MAKE_ROUTING_RPL_LITE
MAKE_NET ?= MAKE_NET_IPV6
MAKE_MAC ?= MAKE_MAC_CSMA

# Compiler Flags
CFLAGS += -DPROJECT_CONF_H=\"project-conf.h\"
CFLAGS += -Wall -Wno-unused-function

# Support building with fixed periodic baseline mode via make flag:
# make sensor-node ADAPTIVE=0
ifeq ($(ADAPTIVE),0)
  CFLAGS += -DADAPTIVE_SAMPLING_ENABLED=0
else
  CFLAGS += -DADAPTIVE_SAMPLING_ENABLED=1
endif

# Clean helper target
clean-all:
	rm -rf *.sky *.cooja *.z1 symbols.c symbols.h obj_* *.log

-include $(CONTIKI)/Makefile.include
