# System Architecture & Technical Specification

## Smart Environmental Monitoring & Energy-Efficient Data Collection in Wireless Sensor Networks (WSN)

---

## 1. Overview & Objectives

Wireless Sensor Networks (WSNs) deployed in environmental, agricultural, and hazardous industrial scenarios are severely constrained by limited battery reserves. The radio transceiver is the dominant energy consumer—often consuming over 100 to 300 times more power than the micro-controller in sleep mode. 

This project implements an end-to-end WSN system that couples **smart environmental sensing** (Temperature, Relative Humidity, Ambient Light, and $\text{CO}_2$ concentration) with an **adaptive, event-driven data collection protocol** on top of the **RPL (Routing Protocol for Low-Power and Lossy Networks)** stack in **Contiki-NG / Cooja**.

### Key Innovations:
1. **Adaptive Delta-Threshold Reporting**: Transmissions are suppressed when environmental physical parameters vary within stability bounds ($|\Delta| < \epsilon$), reducing radio transmissions by **>70%**.
2. **Prioritized Critical Anomaly Dispatch**: Environmental hazards (e.g., wildfire temperature spikes $>45^\circ\text{C}$ or hazardous gas surges $>1200\text{ ppm}$) instantly bypass delta checks and trigger zero-latency emergency transmissions.
3. **Hardware-Accurate Energest Power Profiling**: Continuous accounting of CPU active time, LPM sleep mode, radio transmit (TX), and radio listen (RX) ticks mapped directly to TelosB / Tmote Sky electrical characteristics.
4. **Resilient RPL Routing**: Automatic DODAG topology formation using MRHOF (Minimum Rank with Hysteresis Objective Function) and ETX (Expected Transmission Count).

---

## 2. Network Protocol Stack

```
+-------------------------------------------------------------------+
| APPLICATION LAYER                                                 |
| Smart Environmental Monitoring (Adaptive Sampling, Alerts, Heartbeat)|
+-------------------------------------------------------------------+
| TRANSPORT LAYER                                                   |
| User Datagram Protocol (UDP) - Port 5678                          |
+-------------------------------------------------------------------+
| NETWORK & ROUTING LAYER                                           |
| IPv6 / 6LoWPAN Adaptation Layer                                   |
| RPL (Routing Protocol for Low-Power and Lossy Networks) [RFC 6550]|
| Objective Function: MRHOF (ETX Metric)                            |
+-------------------------------------------------------------------+
| DATA LINK & MAC LAYER                                             |
| IEEE 802.15.4 MAC (CSMA/CA) + ContikiMAC / TSCH Radio Duty Cycling|
+-------------------------------------------------------------------+
| PHYSICAL (PHY) LAYER                                              |
| IEEE 802.15.4 2.4 GHz ISM Band (CC2420 Transceiver @ Channel 26)   |
+-------------------------------------------------------------------+
```

---

## 3. Mathematical Energy Consumption Model

Energy profiling utilizes Contiki's **Energest module**, which intercepts state transitions in the microcontroller and radio driver to accumulate timer ticks:

Let:
- $V = 3.0\text{ V}$ (Supply voltage for Tmote Sky / TelosB motes)
- $I_{\text{cpu}} = 1.8\text{ mA} = 1.8 \times 10^{-3}\text{ A}$ (Active MCU current)
- $I_{\text{lpm}} = 0.0545\text{ mA} = 5.45 \times 10^{-5}\text{ A}$ (Low-Power Mode / Sleep current)
- $I_{\text{tx}} = 17.4\text{ mA} = 1.74 \times 10^{-2}\text{ A}$ (Radio transmission current at 0 dBm)
- $I_{\text{rx}} = 18.8\text{ mA} = 1.88 \times 10^{-2}\text{ A}$ (Radio listen/receive current)
- $f_{\text{rtimer}} = 32768\text{ Hz}$ (MSP430 real-time clock frequency)

The duration spent in each operational state $k \in \{\text{cpu}, \text{lpm}, \text{tx}, \text{rx}\}$ over an evaluation interval is:
$$t_k = \frac{\text{ticks}_k}{f_{\text{rtimer}}} \quad \text{(seconds)}$$

The total energy consumed in milliJoules (mJ) is calculated as:
$$E_{\text{total}} = V \cdot \left[ I_{\text{cpu}} t_{\text{cpu}} + I_{\text{lpm}} t_{\text{lpm}} + I_{\text{tx}} t_{\text{tx}} + I_{\text{rx}} t_{\text{rx}} \right] \times 1000\text{ mJ}$$

Average node power draw $P_{\text{avg}}$ (in milliWatts) over total simulation duration $T_{\text{sim}}$:
$$P_{\text{avg}} = \frac{E_{\text{total}}}{T_{\text{sim}}}$$

Estimated battery lifetime $L_{\text{days}}$ under a standard pair of AA alkaline batteries ($C = 2500\text{ mAh}$ at $3.0\text{ V} \implies E_{\text{batt}} \approx 27{,}000{,}000\text{ mJ}$):
$$L_{\text{days}} = \frac{E_{\text{batt}}}{P_{\text{avg}} \times 1000 \times 86400}$$

---

## 4. Smart Adaptive Data Collection Algorithm

```
Algorithm 1: Adaptive Environmental Sampling & Transmission Control
-------------------------------------------------------------------
Input: Current sample S(t) = {Temp, Humid, Light, CO2}, Last transmitted S_prev
Output: Transmission decision [TRANSMIT_ALERT, TRANSMIT_NORMAL, TRANSMIT_HEARTBEAT, SUPPRESS]

1:  if Temp >= TEMP_CRITICAL or CO2 >= CO2_DANGER then
2:      Set Packet.Type = MSG_TYPE_DATA_ALERT
3:      Flash LED(RED)
4:      return TRANSMIT_ALERT
5:  end if

6:  if S_prev is NULL then
7:      Set Packet.Type = MSG_TYPE_DATA_NORMAL
8:      return TRANSMIT_NORMAL
9:  end if

10: delta_T = |Temp - S_prev.Temp|
11: delta_H = |Humid - S_prev.Humid|
12: delta_L = |Light - S_prev.Light|
13: delta_C = |CO2 - S_prev.CO2|

14: if delta_T >= THRESH_T or delta_H >= THRESH_H or 
       delta_L >= THRESH_L or delta_C >= THRESH_C then
15:     Set Packet.Type = MSG_TYPE_DATA_NORMAL
16:     S_prev = S(t)
17:     return TRANSMIT_NORMAL
18: else if (Current_Time - Last_TX_Time) >= MAX_SILENCE_INTERVAL then
19:     Set Packet.Type = MSG_TYPE_HEARTBEAT
20:     return TRANSMIT_HEARTBEAT
21: else
22:     Suppressed_Counter = Suppressed_Counter + 1
23:     return SUPPRESS
24: end if
```

---

## 5. Packet Format Specification

All telemetry data is encapsulated into a packed 36-byte binary structure `sensor_packet_t`:

| Byte Offset | Field Name | Type | Description |
|:---:|:---|:---|:---|
| 0 - 1 | `node_id` | `uint16_t` | Originating Sensor Node ID |
| 2 - 3 | `seq_num` | `uint16_t` | Monotonically increasing sequence number |
| 4 | `msg_type` | `uint8_t` | 1: NORMAL, 2: ALERT, 3: HEARTBEAT, 4: AGGREGATED |
| 5 | `hop_count` | `uint8_t` | Distance in hops to the RPL DAG root |
| 6 - 7 | `temperature` | `int16_t` | Fixed-point Celsius $\times 100$ ($2540 \implies 25.40^\circ\text{C}$) |
| 8 - 9 | `humidity` | `uint16_t` | Relative Humidity $\% \times 100$ ($6250 \implies 62.50\%$) |
| 10 - 11 | `light_lux` | `uint16_t` | Ambient light level in Lux ($0 - 65535$) |
| 12 - 13 | `co2_ppm` | `uint16_t` | Gas / $\text{CO}_2$ concentration in PPM |
| 14 - 15 | `battery_mv` | `uint16_t` | Estimated node battery voltage in mV |
| 16 - 19 | `cpu_time` | `uint32_t` | Energest CPU active timer ticks |
| 20 - 23 | `lpm_time` | `uint32_t` | Energest Low-Power Mode (LPM) sleep ticks |
| 24 - 27 | `tx_time` | `uint32_t` | Energest Radio Transmit ticks |
| 28 - 31 | `rx_time` | `uint32_t` | Energest Radio Listen/Receive ticks |
