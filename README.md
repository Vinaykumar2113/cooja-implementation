# Smart Environmental Monitoring with Cooja

This project provides a small Contiki/Cooja demonstration of event-driven environmental
monitoring. Sensor motes read simulated temperature and humidity values, report readings
only when a threshold is exceeded or a low-rate heartbeat is due, and send them to a sink
via the Contiki Rime broadcast API.

The same traffic reduction and heartbeat pattern can be used to save radio and sensor
energy in a real wireless sensor network. The implementation is intentionally small and
does not depend on a particular physical sensor board.

## Files

- `smart_sensor.c` - sensor mote application
- `sink.c` - sink mote application
- `Makefile` - builds the motes for Cooja
- `simulation.csc` - Cooja simulation definition

## Requirements

- Contiki-NG or a compatible Contiki 4.x source tree
- Java and Cooja
- GNU Make and an arm/msp430 toolchain as required by your Contiki target

Set `CONTIKI` to the absolute path of your Contiki source tree before building:

```sh
make CONTIKI=/absolute/path/to/contiki TARGET=cooja
```

## Run

1. Open Cooja.
2. Choose **File > Open simulation** and select `simulation.csc`.
3. If Cooja cannot find the mote source files, update the mote source paths in the
   **Mote type** configuration.
4. Start the simulation.

The sink prints received records in the Cooja log. A sensor log line has the form:

```text
DATA node=1 seq=1 temp=240 humidity=550 event=1
```

`temp` is stored in tenths of degrees Celsius and `humidity` in tenths of a percent.

## Energy-saving behavior

- Normal sampling is performed at a low 30-second rate.
- The radio sends only threshold events or a 5-minute heartbeat.
- The sensor state is returned to the low-power path after each sample.
- A sequence number helps the sink detect missing records.
