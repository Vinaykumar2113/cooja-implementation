/*
 * Smart Environmental Monitoring and Energy-Efficient Data Collection in WSN
 * 
 * common-header.h: Shared message definitions, telemetry payload formats,
 * sensor threshold constants, and energy profiling definitions.
 */

#ifndef COMMON_HEADER_H_
#define COMMON_HEADER_H_

#include <stdint.h>

/* UDP Communications Port */
#define UDP_PORT 5678

/* Sink Node Identity */
#define SINK_NODE_ID 1

/* Packet / Message Types (Opcodes) */
#define MSG_TYPE_DATA_NORMAL    1  /* Regular periodic telemetry report */
#define MSG_TYPE_DATA_ALERT     2  /* Event-driven critical alert (immediate TX) */
#define MSG_TYPE_HEARTBEAT      3  /* Lightweight alive / keep-alive heartbeat */
#define MSG_TYPE_AGGREGATED     4  /* Aggregated multi-reading packet */

/* Environmental Thresholds (Scaled for integer fixed-point arithmetic) */
/* Temperature in Celsius * 100 (e.g. 2550 = 25.50 C) */
#define TEMP_THRESHOLD_HIGH     3800  /* 38.00 C - Heat warning */
#define TEMP_THRESHOLD_CRITICAL 4500  /* 45.00 C - Fire / Thermal risk */
#define TEMP_THRESHOLD_FREEZE    200  /*  2.00 C - Frost / Freeze risk */

/* Relative Humidity in % * 100 (e.g. 6000 = 60.00 %) */
#define HUMID_THRESHOLD_LOW     2000  /* 20.00 % - Drought / Arid danger */
#define HUMID_THRESHOLD_HIGH    9000  /* 90.00 % - Flood / Condensation warning */

/* Ambient Light Intensity in Lux */
#define LIGHT_THRESHOLD_DARK      10  /* Night / Sensor blockage */
#define LIGHT_THRESHOLD_BRIGHT  2500  /* Intense solar radiation */

/* Air Quality / CO2 Equivalent in PPM */
#define CO2_THRESHOLD_WARN       800  /* 800 ppm - Poor air circulation */
#define CO2_THRESHOLD_DANGER    1200  /* 1200 ppm - Dangerous / Toxic / Smoke */

/* Adaptive Sampling / Reporting Delta Thresholds */
/* A new packet is transmitted only if reading delta >= threshold, saving radio energy */
#define TEMP_DELTA_THRESHOLD     100  /* 1.00 C change */
#define HUMID_DELTA_THRESHOLD    250  /* 2.50 % change */
#define LIGHT_DELTA_THRESHOLD     80  /* 80 Lux change */
#define CO2_DELTA_THRESHOLD       60  /* 60 PPM change */

/* Telemetry Packet Structure (36 bytes packed) */
typedef struct {
  uint16_t node_id;          /* Originating Node ID */
  uint16_t seq_num;          /* Monotonically increasing sequence number */
  uint8_t  msg_type;         /* MSG_TYPE_* */
  uint8_t  hop_count;        /* Approximate hop distance to sink */
  int16_t  temperature;      /* Centidegrees Celsius (2540 -> 25.40 C) */
  uint16_t humidity;         /* Relative humidity % x 100 (6200 -> 62.00 %) */
  uint16_t light_lux;        /* Light intensity in Lux */
  uint16_t co2_ppm;          /* CO2 / Gas concentration in PPM */
  uint16_t battery_mv;       /* Estimated mote battery voltage in mV */
  uint32_t cpu_time;         /* Energest: CPU active mode ticks */
  uint32_t lpm_time;         /* Energest: Low Power Mode (Sleep) ticks */
  uint32_t tx_time;          /* Energest: Radio Transmit ticks */
  uint32_t rx_time;          /* Energest: Radio Listen / Receive ticks */
} __attribute__((packed)) sensor_packet_t;

/* Aggregated Batch Reading for Multi-Sample Compression */
typedef struct {
  int16_t  temperature;
  uint16_t humidity;
  uint16_t light_lux;
  uint16_t co2_ppm;
  uint16_t timestamp_offset_sec;
} __attribute__((packed)) compact_reading_t;

#define MAX_AGGREGATED_READINGS 3

typedef struct {
  uint16_t node_id;
  uint16_t seq_num;
  uint8_t  msg_type;         /* MSG_TYPE_AGGREGATED */
  uint8_t  reading_count;    /* Number of valid readings (<= MAX) */
  uint16_t battery_mv;
  uint32_t tx_time;
  uint32_t rx_time;
  compact_reading_t readings[MAX_AGGREGATED_READINGS];
} __attribute__((packed)) aggregated_packet_t;

#endif /* COMMON_HEADER_H_ */
