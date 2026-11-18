#include "contiki.h"
#include "net/rime/broadcast.h"

#include <stdio.h>

struct sensor_record {
  uint16_t sequence;
  int16_t temperature_tenths;
  uint16_t humidity_tenths;
};

PROCESS(sink_process, "Environmental data sink");
AUTOSTART_PROCESSES(&sink_process);

static struct broadcast_conn sink_broadcast;

static void broadcast_received(struct broadcast_conn *connection,
                               const linkaddr_t *sender)
{
  struct sensor_record record;

  (void)connection;
  if(packetbuf_datalen() != sizeof(record)) {
    printf("SINK malformed packet bytes=%u\n", packetbuf_datalen());
    return;
  }

  packetbuf_copyto(&record);
  printf("SINK source=%u.%u seq=%u temp=%d humidity=%u\n",
         sender->u8[0],
         sender->u8[1],
         record.sequence,
         record.temperature_tenths,
         record.humidity_tenths);
}

static const struct broadcast_callbacks sink_callbacks = {
  broadcast_received,
  NULL
};

PROCESS_THREAD(sink_process, ev, data)
{
  PROCESS_BEGIN();

  broadcast_open(&sink_broadcast, 146, &sink_callbacks);
  printf("SINK ready\n");

  while(1) {
    PROCESS_WAIT_EVENT();
  }

  PROCESS_END();
}
