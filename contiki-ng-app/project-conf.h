/*
 * Smart Environmental Monitoring and Energy-Efficient Data Collection in WSN
 * 
 * project-conf.h: System-wide configuration for Contiki / Contiki-NG,
 * RPL Routing, Radio Duty Cycling (RDC), and Energest Profiler.
 */

#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

/* Enable Energest Module for software-based energy estimation */
#undef ENERGEST_CONF_ON
#define ENERGEST_CONF_ON 1

/* IPv6 Network Stack Configuration */
#undef UIP_CONF_ROUTER
#define UIP_CONF_ROUTER 1

#undef UIP_CONF_IPV6_RPL
#define UIP_CONF_IPV6_RPL 1

/* Increase packet buffer size to accommodate 6LoWPAN payloads comfortably */
#undef UIP_CONF_BUFFER_SIZE
#define UIP_CONF_BUFFER_SIZE 240

/* RPL Objective Function: MRHOF (Minimum Rank with Hysteresis Objective Function) */
/* MRHOF uses ETX (Expected Transmission Count) metric for energy-efficient routes */
#define RPL_CONF_OF_OCP RPL_OCP_MRHOF

/* ContikiMAC Radio Duty Cycling Configuration (When using classic Contiki) */
#ifdef NETSTACK_CONF_RDC
#define NETSTACK_CONF_RDC contikimac_driver
#define NETSTACK_CONF_MAC csma_driver
#endif

/* Radio Channel Selection (IEEE 802.15.4 Channel 26 to minimize 2.4GHz Wi-Fi interference) */
#undef IEEE802154_CONF_PANID
#define IEEE802154_CONF_PANID 0xABCD

#undef RF_CHANNEL
#define RF_CHANNEL 26

/* Logging Level Configuration */
#define LOG_CONF_LEVEL_RPL                         LOG_LEVEL_INFO
#define LOG_CONF_LEVEL_TCPIP                       LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_IPV6                        LOG_LEVEL_WARN
#define LOG_CONF_LEVEL_MAC                         LOG_LEVEL_WARN

/* Sensor Sampling Intervals (in seconds) */
#define SENSING_INTERVAL_SEC      5    /* Physical sensing sampling period */
#define DEFAULT_REPORT_INTERVAL   15   /* Normal periodic report interval */
#define MAX_REPORT_INTERVAL       60   /* Max allowable silence before heartbeat */
#define MIN_REPORT_INTERVAL        3   /* Min interval between back-to-back alerts */

/* TelosB / Sky Hardware Power Specifications (at 3.0V) */
/* Used for post-simulation analytical energy estimation */
#define TELOSB_VOLTAGE_MV         3000 /* 3.0 Volts */
#define TELOSB_CURRENT_CPU_UA     1800 /* 1.8 mA active CPU */
#define TELOSB_CURRENT_LPM_UA       55 /* ~0.0545 mA sleep mode */
#define TELOSB_CURRENT_TX_UA     17400 /* 17.4 mA radio transmit (0 dBm) */
#define TELOSB_CURRENT_RX_UA     18800 /* 18.8 mA radio listen / receive */

#endif /* PROJECT_CONF_H_ */
