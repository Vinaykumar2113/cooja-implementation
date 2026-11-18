/*
 * Smart Environmental Monitoring and Energy-Efficient Data Collection in WSN
 * 
 * sink-node.c: RPL DAG Root (Border Router) and Central Telemetry Collector.
 * Collects environmental data from sensor nodes, logs metrics for Cooja analysis,
 * calculates Packet Delivery Ratio (PDR), and tracks network health.
 */

#include "contiki.h"
#include "contiki-net.h"
#include "sys/energest.h"
#include "dev/leds.h"
#include "common-header.h"
#include "project-conf.h"

#include <stdio.h>
#include <string.h>

#if __has_include("net/routing/routing.h")
/* Contiki-NG Architecture */
#include "net/routing/routing.h"
#include "net/netstack.h"
#include "net/ipv6/simple-udp.h"
#include "sys/node-id.h"
#define IS_CONTIKI_NG 1
#else
/* Classic Contiki 2.7 / 3.0 Architecture */
#include "net/ip/uip.h"
#include "net/ipv6/uip-ds6.h"
#include "net/rpl/rpl.h"
#include "simple-udp.h"
#include "node-id.h"
#define IS_CONTIKI_NG 0
#endif

#define MAX_TRACKED_NODES 32

typedef struct {
  uint16_t node_id;
  uint16_t last_seq;
  uint32_t packets_received;
  uint32_t packets_lost;
  uint32_t first_seen_sec;
  uint32_t last_seen_sec;
  int16_t  last_temp;
  uint16_t last_humid;
  uint16_t last_light;
  uint16_t last_co2;
  uint16_t last_battery;
  uint32_t last_cpu;
  uint32_t last_lpm;
  uint32_t last_tx;
  uint32_t last_rx;
} node_stats_t;

static node_stats_t tracked_nodes[MAX_TRACKED_NODES];
static uint8_t tracked_node_count = 0;
static uint32_t total_rx_packets = 0;
static uint32_t total_expected_packets = 0;
static struct simple_udp_connection udp_conn;

/*---------------------------------------------------------------------------*/
PROCESS(sink_collector_process, "Smart WSN Sink & DAG Root Process");
AUTOSTART_PROCESSES(&sink_collector_process);
/*---------------------------------------------------------------------------*/

static node_stats_t* get_or_create_node_stats(uint16_t node_id) {
  uint8_t i;
  for (i = 0; i < tracked_node_count; i++) {
    if (tracked_nodes[i].node_id == node_id) {
      return &tracked_nodes[i];
    }
  }
  if (tracked_node_count < MAX_TRACKED_NODES) {
    node_stats_t *entry = &tracked_nodes[tracked_node_count++];
    memset(entry, 0, sizeof(node_stats_t));
    entry->node_id = node_id;
    entry->first_seen_sec = clock_seconds();
    return entry;
  }
  return NULL;
}

/* UDP Reception Callback */
static void udp_rx_callback(struct simple_udp_connection *c,
                            const uip_ipaddr_t *sender_addr,
                            uint16_t sender_port,
                            const uip_ipaddr_t *receiver_addr,
                            uint16_t receiver_port,
                            const uint8_t *data,
                            uint16_t datalen) {
  if (datalen < sizeof(sensor_packet_t)) {
    printf("[SINK-WARN] Received undersized packet: %u bytes\n", datalen);
    return;
  }

  sensor_packet_t packet;
  memcpy(&packet, data, sizeof(sensor_packet_t));

  total_rx_packets++;
  uint32_t now_sec = clock_seconds();

  node_stats_t *st = get_or_create_node_stats(packet.node_id);
  if (st != NULL) {
    if (st->packets_received > 0 && packet.seq_num > st->last_seq + 1) {
      uint16_t missing = packet.seq_num - st->last_seq - 1;
      st->packets_lost += missing;
      total_expected_packets += missing;
    }
    st->last_seq = packet.seq_num;
    st->packets_received++;
    st->last_seen_sec = now_sec;
    st->last_temp = packet.temperature;
    st->last_humid = packet.humidity;
    st->last_light = packet.light_lux;
    st->last_co2 = packet.co2_ppm;
    st->last_battery = packet.battery_mv;
    st->last_cpu = packet.cpu_time;
    st->last_lpm = packet.lpm_time;
    st->last_tx = packet.tx_time;
    st->last_rx = packet.rx_time;
  }
  total_expected_packets++;

  /* Flash LED based on packet type: Red for Alert, Green for Normal */
  if (packet.msg_type == MSG_TYPE_DATA_ALERT) {
    leds_on(LEDS_RED);
    printf("[SINK-ALERT] Time=%lu Node=%u Seq=%u Temp=%d.%02dC Humid=%u.%02u%% Light=%ulux CO2=%uppm Batt=%umV Hops=%u (CRITICAL EVENT)\n",
           (unsigned long)now_sec,
           packet.node_id,
           packet.seq_num,
           packet.temperature / 100, (packet.temperature < 0 ? -packet.temperature : packet.temperature) % 100,
           packet.humidity / 100, packet.humidity % 100,
           packet.light_lux,
           packet.co2_ppm,
           packet.battery_mv,
           packet.hop_count);
  } else {
    leds_on(LEDS_GREEN);
    const char *type_str = (packet.msg_type == MSG_TYPE_HEARTBEAT) ? "HEARTBEAT" : "NORMAL";
    printf("[SINK-DATA] Time=%lu Node=%u Seq=%u Type=%s Temp=%d.%02dC Humid=%u.%02u%% Light=%ulux CO2=%uppm Batt=%umV Hops=%u Energest[CPU=%lu LPM=%lu TX=%lu RX=%lu]\n",
           (unsigned long)now_sec,
           packet.node_id,
           packet.seq_num,
           type_str,
           packet.temperature / 100, (packet.temperature < 0 ? -packet.temperature : packet.temperature) % 100,
           packet.humidity / 100, packet.humidity % 100,
           packet.light_lux,
           packet.co2_ppm,
           packet.battery_mv,
           packet.hop_count,
           (unsigned long)packet.cpu_time,
           (unsigned long)packet.lpm_time,
           (unsigned long)packet.tx_time,
           (unsigned long)packet.rx_time);
  }

  clock_delay_usec(2000);
  leds_off(LEDS_ALL);
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(sink_collector_process, ev, data) {
  static struct etimer periodic_timer;
  static uip_ipaddr_t prefix;

  PROCESS_BEGIN();

  printf("=================================================================\n");
  printf("  SMART ENVIRONMENTAL MONITORING & ENERGY-EFFICIENT WSN SINK     \n");
  printf("  Node ID: %u | Target: RPL DAG Root Collector                   \n", node_id);
  printf("=================================================================\n");

  /* Initialize RPL DAG Root / Border Router */
#if IS_CONTIKI_NG
  NETSTACK_ROUTING.root_start();
#else
  uip_ip6addr(&prefix, 0xfd00, 0, 0, 0, 0, 0, 0, 0);
  rpl_set_root(RPL_DEFAULT_INSTANCE, &prefix);
  rpl_dag_t *dag = rpl_get_any_dag();
  if (dag != NULL) {
    rpl_set_prefix(dag, &prefix, 64);
    printf("[SINK-INIT] RPL DAG root created with prefix fd00::/64\n");
  }
#endif

  /* Initialize UDP listener */
  simple_udp_register(&udp_conn, UDP_PORT, NULL, UDP_PORT, udp_rx_callback);
  printf("[SINK-INIT] Listening on UDP port %d for sensor reports\n", UDP_PORT);

  etimer_set(&periodic_timer, CLOCK_SECOND * 60);

  while (1) {
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

    /* Periodic Network Diagnostics & Health Summary */
    uint32_t now_sec = clock_seconds();
    float global_pdr = (total_expected_packets > 0) ? 
                       ((float)total_rx_packets / (float)total_expected_packets * 100.0f) : 100.0f;

    printf("\n--- [NETWORK-SUMMARY @ %lu s] ---\n", (unsigned long)now_sec);
    printf("Total Nodes Registered: %u\n", tracked_node_count);
    printf("Total Packets Received: %lu | Total Expected: %lu | Global PDR: %.2f%%\n",
           (unsigned long)total_rx_packets, (unsigned long)total_expected_packets, global_pdr);

    uint8_t i;
    for (i = 0; i < tracked_node_count; i++) {
      node_stats_t *s = &tracked_nodes[i];
      uint32_t expected = s->packets_received + s->packets_lost;
      float node_pdr = (expected > 0) ? ((float)s->packets_received / (float)expected * 100.0f) : 100.0f;
      printf("  Node %2u: PktsRecv=%-4lu Lost=%-3lu PDR=%.1f%% LastSeen=%-4lus Temp=%2d.%02dC Batt=%4umV\n",
             s->node_id,
             (unsigned long)s->packets_received,
             (unsigned long)s->packets_lost,
             node_pdr,
             (unsigned long)(now_sec - s->last_seen_sec),
             s->last_temp / 100, (s->last_temp < 0 ? -s->last_temp : s->last_temp) % 100,
             s->last_battery);
    }
    printf("------------------------------------\n\n");

    etimer_reset(&periodic_timer);
  }

  PROCESS_END();
}
