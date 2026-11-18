/*
 * Smart Environmental Monitoring and Energy-Efficient Data Collection in WSN
 * 
 * sensor-node.c: Environmental Sensing Mote with Smart Adaptive Data Collection
 * and Energest Radio Profiling.
 * 
 * Features:
 * - Dynamic / Adaptive Delta-Threshold Transmission
 * - Critical Anomaly / Event-Driven Immediate Reporting (Wildfire/Smoke Alert)
 * - Radio Duty Cycling & Sleep Scheduling
 * - Real-time Energest CPU & Radio Energy Metrics
 */

#include "contiki.h"
#include "contiki-net.h"
#include "sys/energest.h"
#include "dev/leds.h"
#include "random.h"
#include "common-header.h"
#include "project-conf.h"

#include <stdio.h>
#include <string.h>

#if __has_include("net/routing/routing.h")
#include "net/routing/routing.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "sys/node-id.h"
#define IS_CONTIKI_NG 1
#else
#include "net/ip/uip.h"
#include "net/ipv6/uip-ds6.h"
#include "net/rpl/rpl.h"
#include "simple-udp.h"
#include "node-id.h"
#define IS_CONTIKI_NG 0
#endif

/* Set to 1 for Smart Energy-Efficient Adaptive Mode; 0 for Baseline Fixed Periodic */
#ifndef ADAPTIVE_SAMPLING_ENABLED
#define ADAPTIVE_SAMPLING_ENABLED 1
#endif

static struct simple_udp_connection udp_conn;
static uip_ipaddr_t sink_ipaddr;

static uint16_t current_seq = 0;
static uint16_t battery_mv = 3000; /* Starting battery voltage 3.0V */

/* Historical readings for delta-threshold calculation */
static int16_t  last_sent_temp = -999;
static uint16_t last_sent_humid = 0;
static uint16_t last_sent_light = 0;
static uint16_t last_sent_co2 = 0;
static uint32_t last_tx_timestamp = 0;

/* Running count of transmissions saved vs performed */
static uint32_t total_samples_taken = 0;
static uint32_t total_packets_transmitted = 0;
static uint32_t transmissions_suppressed = 0;

/* Helper absolute difference */
static int16_t abs_diff16(int16_t a, int16_t b) {
  int16_t diff = a - b;
  return (diff < 0) ? -diff : diff;
}

/* Emulated Environmental Sensing Engine */
static void read_environmental_sensors(int16_t *temp, uint16_t *humid, uint16_t *light, uint16_t *co2) {
  uint32_t now = clock_seconds();
  
  /* Baseline environmental values */
  int16_t base_temp = 2400 + (node_id * 35); /* ~24.0C to 27.0C */
  uint16_t base_humid = 5500 - (node_id * 50); /* ~50% to 55% */
  uint16_t base_light = 350 + (node_id * 20);  /* ~350 to 500 Lux */
  uint16_t base_co2 = 400 + (node_id * 15);    /* ~400 to 520 PPM */

  /* Diurnal fluctuation simulation using clock seconds */
  int16_t cycle = (int16_t)((now % 180) - 90); /* -90 to +90 */
  int16_t noise = (int16_t)((random_rand() % 31) - 15); /* Small measurement noise */

  *temp = base_temp + (cycle * 2) + noise;
  *humid = base_humid - cycle + (noise * 2);
  *light = base_light + (cycle * 4) + noise;
  *co2 = base_co2 + (noise / 2);

  /* Simulated Fire / Environmental Anomaly Event:
   * Node 4 experiences severe temperature surge and smoke spike after 120s */
  if (node_id == 4 && now >= 120 && now <= 280) {
    *temp += 2300; /* Surges past 47.00 C! */
    *co2 += 850;   /* Surges past 1250 PPM! */
    *humid = (*humid > 1500) ? (*humid - 1500) : 500; /* Drop in humidity */
  }

  /* Natural battery gradual discharge */
  if (battery_mv > 2400 && (total_samples_taken % 20 == 0)) {
    battery_mv -= 1;
  }
}

/* Estimate Energy Consumption in MilliJoules using TelosB Specs */
static void print_energy_profile(uint32_t cpu, uint32_t lpm, uint32_t tx, uint32_t rx) {
  /* TelosB: 3V supply. Energy (mJ) = Voltage * Current * (Ticks / RTIMER_ARCH_SECOND) * 1000 */
  uint32_t rtimer_sec = RTIMER_ARCH_SECOND;
  if (rtimer_sec == 0) rtimer_sec = 32768;

  double e_cpu = (3.0 * 0.0018 * cpu) / rtimer_sec * 1000.0;
  double e_lpm = (3.0 * 0.000055 * lpm) / rtimer_sec * 1000.0;
  double e_tx  = (3.0 * 0.0174 * tx) / rtimer_sec * 1000.0;
  double e_rx  = (3.0 * 0.0188 * rx) / rtimer_sec * 1000.0;
  double e_tot = e_cpu + e_lpm + e_tx + e_rx;

  printf("[ENERGY-MOTE-%u] Total_mJ=%.2f (CPU=%.2f, LPM=%.2f, TX=%.2f, RX=%.2f)\n",
         node_id, e_tot, e_cpu, e_lpm, e_tx, e_rx);
}

/*---------------------------------------------------------------------------*/
PROCESS(sensor_node_process, "Smart Environmental Sensor Process");
AUTOSTART_PROCESSES(&sensor_node_process);
/*---------------------------------------------------------------------------*/

PROCESS_THREAD(sensor_node_process, ev, data) {
  static struct etimer sample_timer;
  static sensor_packet_t packet;

  PROCESS_BEGIN();

  printf("=================================================================\n");
  printf("  SMART ENVIRONMENTAL SENSOR NODE INITIALIZING                   \n");
  printf("  Node ID: %u | Mode: %s\n", 
         node_id,
         ADAPTIVE_SAMPLING_ENABLED ? "ENERGY-EFFICIENT ADAPTIVE" : "FIXED PERIODIC BASELINE");
  printf("=================================================================\n");

  /* Setup Destination Sink Address: fd00::1 */
  uip_ip6addr(&sink_ipaddr, 0xfd00, 0, 0, 0, 0, 0, 0, 1);

  /* Initialize UDP connection */
  simple_udp_register(&udp_conn, UDP_PORT, NULL, UDP_PORT, NULL);

  /* Stagger initial sampling to avoid initial boot transmission collisions */
  etimer_set(&sample_timer, CLOCK_SECOND * 5 + (random_rand() % (CLOCK_SECOND * 5)));
  PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&sample_timer));

  printf("[NODE-%u] Sensing loop active. Ready to transmit.\n", node_id);

  while (1) {
    etimer_set(&sample_timer, CLOCK_SECOND * SENSING_INTERVAL_SEC);
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&sample_timer));

    total_samples_taken++;
    uint32_t now_sec = clock_seconds();

    int16_t  temp;
    uint16_t humid, light, co2;
    read_environmental_sensors(&temp, &humid, &light, &co2);

    /* Determine transmission necessity */
    uint8_t must_transmit = 0;
    uint8_t msg_type = MSG_TYPE_DATA_NORMAL;

    /* 1. Critical Event / Hazard Check (Always highest priority) */
    if (temp >= TEMP_THRESHOLD_CRITICAL || co2 >= CO2_THRESHOLD_DANGER) {
      must_transmit = 1;
      msg_type = MSG_TYPE_DATA_ALERT;
      leds_on(LEDS_RED);
      printf("[ALERT-EVENT] Node %u detected critical hazard! Temp=%d.%02dC CO2=%uppm\n",
             node_id, temp / 100, (temp < 0 ? -temp : temp) % 100, co2);
    }
#if ADAPTIVE_SAMPLING_ENABLED
    /* 2. Adaptive Delta-Threshold Check */
    else if (last_sent_temp == -999) {
      /* First sample always transmitted to establish baseline */
      must_transmit = 1;
      msg_type = MSG_TYPE_DATA_NORMAL;
    } else {
      int16_t d_temp  = abs_diff16(temp, last_sent_temp);
      int16_t d_humid = abs_diff16(humid, last_sent_humid);
      int16_t d_light = abs_diff16(light, last_sent_light);
      int16_t d_co2   = abs_diff16(co2, last_sent_co2);

      if (d_temp >= TEMP_DELTA_THRESHOLD ||
          d_humid >= HUMID_DELTA_THRESHOLD ||
          d_light >= LIGHT_DELTA_THRESHOLD ||
          d_co2 >= CO2_DELTA_THRESHOLD) {
        must_transmit = 1;
        msg_type = MSG_TYPE_DATA_NORMAL;
      } else if ((now_sec - last_tx_timestamp) >= MAX_REPORT_INTERVAL) {
        /* Keep-alive heartbeat when values remain stable */
        must_transmit = 1;
        msg_type = MSG_TYPE_HEARTBEAT;
      } else {
        /* Delta is below threshold and heartbeat timeout not reached: SUPPRESS TX! */
        transmissions_suppressed++;
        must_transmit = 0;
      }
    }
#else
    /* Fixed Periodic Mode: Always transmit every sample interval */
    must_transmit = 1;
    msg_type = MSG_TYPE_DATA_NORMAL;
#endif

    if (must_transmit) {
      energest_flush();
      uint32_t cpu = energest_type_time(ENERGEST_TYPE_CPU);
      uint32_t lpm = energest_type_time(ENERGEST_TYPE_LPM);
      uint32_t tx  = energest_type_time(ENERGEST_TYPE_TRANSMIT);
      uint32_t rx  = energest_type_time(ENERGEST_TYPE_LISTEN);

      /* Build Packet */
      packet.node_id = node_id;
      packet.seq_num = ++current_seq;
      packet.msg_type = msg_type;
      packet.hop_count = 1; /* Initial hop; decremented/incremented by forwarders */
      packet.temperature = temp;
      packet.humidity = humid;
      packet.light_lux = light;
      packet.co2_ppm = co2;
      packet.battery_mv = battery_mv;
      packet.cpu_time = cpu;
      packet.lpm_time = lpm;
      packet.tx_time = tx;
      packet.rx_time = rx;

      /* Transmit via UDP Unicast to Sink */
      simple_udp_sendto(&udp_conn, &packet, sizeof(packet), &sink_ipaddr);
      total_packets_transmitted++;

      /* Update historical reference */
      last_sent_temp = temp;
      last_sent_humid = humid;
      last_sent_light = light;
      last_sent_co2 = co2;
      last_tx_timestamp = now_sec;

      leds_on(LEDS_BLUE);
      printf("[TX] Node=%u Seq=%u Type=%s Temp=%d.%02dC Humid=%u.%02u%% Light=%u CO2=%u Batt=%umV Suppressed=%lu\n",
             node_id, current_seq,
             (msg_type == MSG_TYPE_DATA_ALERT) ? "ALERT" : (msg_type == MSG_TYPE_HEARTBEAT ? "HEARTBEAT" : "DATA"),
             temp / 100, (temp < 0 ? -temp : temp) % 100,
             humid / 100, humid % 100,
             light, co2, battery_mv,
             (unsigned long)transmissions_suppressed);
      
      clock_delay_usec(1000);
      leds_off(LEDS_ALL);
    }

    /* Periodic profiling report every 60 seconds */
    if (total_samples_taken % 12 == 0) {
      energest_flush();
      uint32_t cpu = energest_type_time(ENERGEST_TYPE_CPU);
      uint32_t lpm = energest_type_time(ENERGEST_TYPE_LPM);
      uint32_t tx  = energest_type_time(ENERGEST_TYPE_TRANSMIT);
      uint32_t rx  = energest_type_time(ENERGEST_TYPE_LISTEN);
      print_energy_profile(cpu, lpm, tx, rx);

      float saving_rate = (total_samples_taken > 0) ?
                          ((float)transmissions_suppressed / (float)total_samples_taken * 100.0f) : 0.0f;
      printf("[MOTE-%u-EFFICIENCY] Samples=%lu Transmitted=%lu Suppressed=%lu RadioSaving=%.1f%%\n",
             node_id,
             (unsigned long)total_samples_taken,
             (unsigned long)total_packets_transmitted,
             (unsigned long)transmissions_suppressed,
             saving_rate);
    }
  }

  PROCESS_END();
}
