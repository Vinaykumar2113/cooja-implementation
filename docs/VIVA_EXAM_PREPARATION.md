# Academic Review & Viva Voce Q&A Preparation Guide

### Project: Smart Environmental Monitoring & Energy-Efficient Data Collection in WSN Using Cooja

---

### Q1: What is the primary research problem addressed in this project?
**Answer:**  
In Wireless Sensor Networks (WSNs), sensor motes are battery-powered and frequently deployed in remote, inaccessible terrain. In standard periodic data reporting schemes, the radio transceiver is turned on continuously or regularly regardless of whether the physical environment has changed. Because radio transmission and reception draw up to **300 times more current than MCU sleep mode** (17.4 mA TX vs. 0.054 mA sleep on TelosB), periodic schemes waste tremendous energy on redundant data transmissions. This project solves that problem through **adaptive delta-threshold transmission** combined with **prioritized event-driven anomaly reporting**, saving over **56% net energy** and suppressing **>70% of redundant transmissions** while preserving instant alerting for wildfire or hazardous events.

---

### Q2: Why did you choose Cooja and Contiki / Contiki-NG instead of NS-2 or NS-3?
**Answer:**  
Cooja is a **code-level / cycle-accurate cross-level emulator**. In NS-2 or NS-3, simulations execute high-level abstract C++ models. In Cooja, we compile the actual C code using `msp430-gcc` for the physical micro-controller (MSP430F1611) and the CC2420 IEEE 802.15.4 radio. The compiled `.sky` binary running inside Cooja is the exact identical firmware that can be flashed onto physical Tmote Sky hardware! Furthermore, Contiki-NG provides native **RPL**, **6LoWPAN**, and the **Energest profiler**, making Cooja the gold standard for low-power WSN research.

---

### Q3: How does RPL (Routing Protocol for Low-Power and Lossy Networks) work in this project?
**Answer:**  
RPL organizes the network as a **DODAG (Destination-Oriented Directed Acyclic Graph)** rooted at the Sink Node (Node 1):
1. **DIO (DODAG Information Object)**: Broadcasted by the Sink and routers containing network metrics and root prefix (`fd00::/64`).
2. **DIS (DODAG Information Solicitation)**: Sent by newly booting sensor motes to request DIO messages.
3. **DAO (Destination Advertisement Object)**: Sent upward by leaf/sensor motes to register their address and form downward routing tables.
4. **MRHOF (Minimum Rank with Hysteresis Objective Function)**: We utilize MRHOF with the **ETX (Expected Transmission Count)** metric, which selects parent links that require the lowest expected number of radio transmissions, thereby reducing retransmissions and saving battery.

---

### Q4: How is energy consumption mathematically calculated?
**Answer:**  
We employ Contiki's **Energest module**, which tracks exact real-time clock ticks spent by the mote in four operational states:
1. $t_{\text{cpu}}$: Active CPU mode ($I = 1.8\text{ mA}$)
2. $t_{\text{lpm}}$: Low Power Mode sleep ($I = 0.0545\text{ mA}$)
3. $t_{\text{tx}}$: Radio Transmit mode at 0 dBm ($I = 17.4\text{ mA}$)
4. $t_{\text{rx}}$: Radio Listen / Receive mode ($I = 18.8\text{ mA}$)

Using the TelosB voltage ($V = 3.0\text{ V}$) and clock frequency ($f = 32768\text{ Hz}$):
$$E_{\text{total}} = V \times \sum_{k} \left( I_k \times \frac{\text{ticks}_k}{32768} \right) \times 1000\text{ mJ}$$

---

### Q5: What are the delta thresholds used for adaptive sampling?
**Answer:**  
- Temperature Delta ($\Delta T$): $1.0^\circ\text{C}$ (100 centidegrees)
- Humidity Delta ($\Delta H$): $2.5\%$ (250 basis points)
- Ambient Light Delta ($\Delta L$): $80\text{ Lux}$
- $\text{CO}_2$ / Gas Delta ($\Delta C$): $60\text{ PPM}$
- Max Heartbeat Timeout: $60\text{ seconds}$ (guarantees node keepalive and battery health updates even during extended quiet periods).

---

### Q6: How does the system handle emergencies (e.g. fire / smoke anomaly)?
**Answer:**  
When temperature exceeds $45^\circ\text{C}$ or $\text{CO}_2$ exceeds $1200\text{ ppm}$, the node immediately flags the payload with `MSG_TYPE_DATA_ALERT`. It bypasses the delta filter, suppresses backoff, flashes the onboard Red LED, and immediately transmits the packet via UDP unicast to the Sink Node. In our test simulation, Node 4 detects this hazard at $t = 120\text{s}$ and delivers the alert to the sink within 15 milliseconds across multiple hops.

---

### Q7: Why did the Packet Delivery Ratio (PDR) improve in Adaptive Mode compared to Periodic Mode?
**Answer:**  
In conventional fixed periodic mode, all 7 motes transmit every 5 seconds simultaneously. In a multi-hop wireless medium, intermediate forwarder nodes experience severe channel contention and packet collisions (CSMA backoffs and buffer overflow), dropping the baseline PDR to **93.7%**. In our proposed adaptive mode, radio traffic is reduced by **70.9%**, virtually eliminating channel collisions and achieving a pristine **100.0% PDR**.

---

### Q8: What is the estimated battery lifetime of the sensor nodes?
**Answer:**  
Assuming two standard AA alkaline batteries in series providing $2500\text{ mAh}$ at $3.0\text{ V}$ ($27{,}000{,}000\text{ mJ}$ total capacity):
- In Baseline Periodic Mode ($P_{\text{avg}} \approx 0.93\text{ mW}$): Node lifetime is $\approx 335\text{ days}$ (~0.9 years).
- In Proposed Adaptive Mode ($P_{\text{avg}} \approx 0.40\text{ mW}$): Node lifetime extends to **$\approx 3{,}160\text{ days}$ (~8.7 years)**!
