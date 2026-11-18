#include "contiki.h"
#include "net/rime/broadcast.h"
#include "random.h"

#include <stdio.h>

#define SAMPLE_INTERVAL_SECONDS 30
#define HEARTBEAT_SECONDS 300
#define TEMPERATURE_THRESHOLD_HIGH 300
#define TEMPERATURE_THRESHOLD_LOW 150

struct sensor_record {
  uint16_t sequence;
  int16_t temperature_tenths;
  uint16_t humidity_tenths;
};

PROCESS(smart_sensor_process, "Smart environmental sensor");
AUTOSTART_PROCESSES(&smart_sensor_process);

static struct broadcast_conn sensor_broadcast;
static struct sensor_record last_record;
static struct sensor_record previous_record;
static uint32_t seconds_since_heartbeat;
static uint8_t initialized;

static void broadcast_received(struct broadcast_conn *connection,
                               const linkaddr_t *sender)
{
  (void)connection;
  (void)sender;
}

static const struct broadcast_callbacks sensor_callbacks = {
  broadcast_received,
  NULL
};

static int16_t read_temperature(void)
{
  /* Simulated sensor. Replace this body with the target board sensor API. */
  return 240 + ((int16_t)(random_rand() % 151) - 75);
}

static uint16_t read_humidity(void)
{
  /* Simulated sensor. Replace this body with the target board sensor API. */
  return 550 + (random_rand() % 101);
}

static uint8_t event_or_heartbeat(struct sensor_record *record)
{
  uint8_t threshold_event =
      record->temperature_tenths > TEMPERATURE_THRESHOLD_HIGH ||
      record->temperature_tenths < TEMPERATURE_THRESHOLD_LOW ||
      record->humidity_tenths > 650 ||
      record->humidity_tenths < 350;

  if(!initialized) {
    return 1;
  }

  if(seconds_since_heartbeat >= HEARTBEAT_SECONDS) {
    seconds_since_heartbeat = 0;
    return 1;
  }

  return threshold_event;
}

PROCESS_THREAD(smart_sensor_process, ev, data)
{
  static struct etimer sample_timer;

  PROCESS_EXITHANDLER(broadcast_close(&sensor_broadcast));
  PROCESS_BEGIN();

  broadcast_open(&sensor_broadcast, 146, &sensor_callbacks);

  while(1) {
    etimer_set(&sample_timer, CLOCK_SECOND * SAMPLE_INTERVAL_SECONDS);
    PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&sample_timer));

    previous_record = last_record;
    last_record.sequence++;
    last_record.temperature_tenths = read_temperature();
    last_record.humidity_tenths = read_humidity();
    seconds_since_heartbeat += SAMPLE_INTERVAL_SECONDS;

    if(event_or_heartbeat(&last_record)) {
      packetbuf_clear();
      packetbuf_copyfrom(&last_record, sizeof(last_record));
      broadcast_send(&sensor_broadcast);

      printf("DATA node=%u seq=%u temp=%d humidity=%u event=1\n",
             linkaddr_node_addr.u8[0],
             last_record.sequence,
             last_record.temperature_tenths,
             last_record.humidity_tenths);
    }

    initialized = 1;
  }

  PROCESS_END();
}
