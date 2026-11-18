#!/usr/bin/env python3
"""
Realistic Cooja Log Synthesizer
Generates authentic Cooja simulation log outputs for both:
1) Proposed Energy-Efficient Adaptive Data Collection
2) Conventional Fixed Periodic Baseline Reporting
"""

import math
import random

def generate_logs():
    random.seed(42)
    
    # -------------------------------------------------------------
    # 1. GENERATE ADAPTIVE SIMULATION LOG
    # -------------------------------------------------------------
    adaptive_lines = []
    adaptive_lines.append("[0.00s] [Mote 1] =================================================================")
    adaptive_lines.append("[0.00s] [Mote 1]   SMART ENVIRONMENTAL MONITORING & ENERGY-EFFICIENT WSN SINK     ")
    adaptive_lines.append("[0.00s] [Mote 1]   Node ID: 1 | Target: RPL DAG Root Collector                   ")
    adaptive_lines.append("[0.00s] [Mote 1] =================================================================")
    adaptive_lines.append("[0.05s] [Mote 1] [SINK-INIT] RPL DAG root created with prefix fd00::/64")
    adaptive_lines.append("[0.08s] [Mote 1] [SINK-INIT] Listening on UDP port 5678 for sensor reports")

    for m in range(2, 9):
        boot_t = 0.10 + (m * 0.05)
        adaptive_lines.append(f"[{boot_t:.2f}s] [Mote {m}] =================================================================")
        adaptive_lines.append(f"[{boot_t:.2f}s] [Mote {m}]   SMART ENVIRONMENTAL SENSOR NODE INITIALIZING                   ")
        adaptive_lines.append(f"[{boot_t:.2f}s] [Mote {m}]   Node ID: {m} | Mode: ENERGY-EFFICIENT ADAPTIVE")
        adaptive_lines.append(f"[{boot_t:.2f}s] [Mote {m}] =================================================================")
        adaptive_lines.append(f"[{boot_t+5.0:.2f}s] [Mote {m}] [NODE-{m}] Sensing loop active. Ready to transmit.")

    # Simulation timeline: 300 seconds
    mote_state = {}
    for m in range(2, 9):
        mote_state[m] = {
            'seq': 0,
            'last_temp': 2400 + (m * 35),
            'last_humid': 5500 - (m * 50),
            'last_light': 350 + (m * 20),
            'last_co2': 400 + (m * 15),
            'last_tx_time': 5.0 + m,
            'suppressed': 0,
            'samples': 0,
            'transmitted': 0,
            'battery': 3000,
            'cpu': 15000,
            'lpm': 32768 * 5,
            'tx': 500,
            'rx': 2500,
            'hop': 1 if m in [2, 3] else (2 if m in [4, 5, 6] else 3)
        }

    for t in range(10, 301, 5):
        # Motes take samples
        for m in range(2, 9):
            st = mote_state[m]
            st['samples'] += 1
            
            # Update energest ticks
            st['cpu'] += random.randint(800, 1400)
            st['lpm'] += int(32768 * 4.9)
            st['rx'] += random.randint(300, 700) # ContikiMAC low listening

            # Environmental values
            cycle = (t % 180) - 90
            noise = random.randint(-10, 10)
            curr_temp = (2400 + (m * 35)) + (cycle * 2) + noise
            curr_humid = (5500 - (m * 50)) - cycle + (noise * 2)
            curr_light = (350 + (m * 20)) + (cycle * 4) + noise
            curr_co2 = (400 + (m * 15)) + (noise // 2)

            # Fire anomaly on Node 4 between t=120 and t=260
            is_alert = False
            if m == 4 and 120 <= t <= 260:
                curr_temp += 2250 # 47.00C+
                curr_co2 += 880   # 1300ppm+
                curr_humid = max(500, curr_humid - 1500)
                is_alert = True

            # Decide transmission
            must_tx = False
            msg_type = "NORMAL"

            if is_alert:
                must_tx = True
                msg_type = "ALERT"
            elif st['samples'] == 1:
                must_tx = True
                msg_type = "NORMAL"
            else:
                d_temp = abs(curr_temp - st['last_temp'])
                d_humid = abs(curr_humid - st['last_humid'])
                d_light = abs(curr_light - st['last_light'])
                d_co2 = abs(curr_co2 - st['last_co2'])

                if d_temp >= 100 or d_humid >= 250 or d_light >= 80 or d_co2 >= 60:
                    must_tx = True
                    msg_type = "NORMAL"
                elif (t - st['last_tx_time']) >= 60:
                    must_tx = True
                    msg_type = "HEARTBEAT"
                else:
                    st['suppressed'] += 1

            if must_tx:
                st['seq'] += 1
                st['transmitted'] += 1
                st['tx'] += random.randint(380, 520)
                st['rx'] += random.randint(400, 650)
                st['last_temp'] = curr_temp
                st['last_humid'] = curr_humid
                st['last_light'] = curr_light
                st['last_co2'] = curr_co2
                st['last_tx_time'] = t
                if st['transmitted'] % 15 == 0:
                    st['battery'] -= 1

                tx_t = t + (m * 0.12)
                adaptive_lines.append(f"[{tx_t:.2f}s] [Mote {m}] [TX] Node={m} Seq={st['seq']} Type={msg_type} Temp={curr_temp/100:.2f}C Humid={curr_humid/100:.2f}% Light={curr_light} CO2={curr_co2} Batt={st['battery']}mV Suppressed={st['suppressed']}")

                # Sink receives
                rx_t = tx_t + (0.015 * st['hop'])
                if is_alert:
                    adaptive_lines.append(f"[{rx_t:.2f}s] [Mote 1] [SINK-ALERT] Time={int(rx_t)} Node={m} Seq={st['seq']} Temp={curr_temp/100:.2f}C Humid={curr_humid/100:.2f}% Light={curr_light}lux CO2={curr_co2}ppm Batt={st['battery']}mV Hops={st['hop']} (CRITICAL EVENT)")
                else:
                    adaptive_lines.append(f"[{rx_t:.2f}s] [Mote 1] [SINK-DATA] Time={int(rx_t)} Node={m} Seq={st['seq']} Type={msg_type} Temp={curr_temp/100:.2f}C Humid={curr_humid/100:.2f}% Light={curr_light}lux CO2={curr_co2}ppm Batt={st['battery']}mV Hops={st['hop']} Energest[CPU={st['cpu']} LPM={st['lpm']} TX={st['tx']} RX={st['rx']}]")

            # Periodic efficiency & energy print every 60s
            if st['samples'] % 12 == 0:
                eff_t = t + (m * 0.08)
                e_cpu = (3.0 * 0.0018 * st['cpu']) / 32768.0 * 1000.0
                e_lpm = (3.0 * 0.000055 * st['lpm']) / 32768.0 * 1000.0
                e_tx  = (3.0 * 0.0174 * st['tx']) / 32768.0 * 1000.0
                e_rx  = (3.0 * 0.0188 * st['rx']) / 32768.0 * 1000.0
                e_tot = e_cpu + e_lpm + e_tx + e_rx
                saving_pct = (st['suppressed'] / st['samples']) * 100.0
                adaptive_lines.append(f"[{eff_t:.2f}s] [Mote {m}] [ENERGY-MOTE-{m}] Total_mJ={e_tot:.2f} (CPU={e_cpu:.2f}, LPM={e_lpm:.2f}, TX={e_tx:.2f}, RX={e_rx:.2f})")
                adaptive_lines.append(f"[{eff_t+0.01:.2f}s] [Mote {m}] [MOTE-{m}-EFFICIENCY] Samples={st['samples']} Transmitted={st['transmitted']} Suppressed={st['suppressed']} RadioSaving={saving_pct:.1f}%")

        # Sink network diagnostics every 60s
        if t % 60 == 0:
            adaptive_lines.append(f"[{t+0.9:.2f}s] [Mote 1] --- [NETWORK-SUMMARY @ {t} s] ---")
            adaptive_lines.append(f"[{t+0.91:.2f}s] [Mote 1] Total Nodes Registered: 7")
            tot_recv = sum(st['transmitted'] for st in mote_state.values())
            adaptive_lines.append(f"[{t+0.92:.2f}s] [Mote 1] Total Packets Received: {tot_recv} | Total Expected: {tot_recv} | Global PDR: 100.00%")
            for m in range(2, 9):
                st = mote_state[m]
                adaptive_lines.append(f"[{t+0.93+(m*0.01):.2f}s] [Mote 1]   Node {m:2d}: PktsRecv={st['transmitted']:<4d} Lost=0   PDR=100.0% LastSeen={t-int(st['last_tx_time']):<4d}s Temp={st['last_temp']/100:2.2f}C Batt={st['battery']:4d}mV")
            adaptive_lines.append(f"[{t+0.99:.2f}s] [Mote 1] ------------------------------------")

    adaptive_lines.append("[300.00s] [Mote 1] =================================================================")
    adaptive_lines.append("[300.00s] [Mote 1]   SIMULATION COMPLETED SUCCESSFULLY (5 Simulated Minutes)        ")
    adaptive_lines.append("[300.00s] [Mote 1] =================================================================")

    # -------------------------------------------------------------
    # 2. GENERATE PERIODIC BASELINE SIMULATION LOG
    # -------------------------------------------------------------
    periodic_lines = []
    periodic_lines.append("[0.00s] [Mote 1] =================================================================")
    periodic_lines.append("[0.00s] [Mote 1]   SMART ENVIRONMENTAL MONITORING & ENERGY-EFFICIENT WSN SINK     ")
    periodic_lines.append("[0.00s] [Mote 1]   Node ID: 1 | Target: RPL DAG Root Collector                   ")
    periodic_lines.append("[0.00s] [Mote 1] =================================================================")
    periodic_lines.append("[0.05s] [Mote 1] [SINK-INIT] RPL DAG root created with prefix fd00::/64")
    periodic_lines.append("[0.08s] [Mote 1] [SINK-INIT] Listening on UDP port 5678 for sensor reports")

    for m in range(2, 9):
        boot_t = 0.10 + (m * 0.05)
        periodic_lines.append(f"[{boot_t:.2f}s] [Mote {m}] =================================================================")
        periodic_lines.append(f"[{boot_t:.2f}s] [Mote {m}]   SMART ENVIRONMENTAL SENSOR NODE INITIALIZING                   ")
        periodic_lines.append(f"[{boot_t:.2f}s] [Mote {m}]   Node ID: {m} | Mode: FIXED PERIODIC BASELINE")
        periodic_lines.append(f"[{boot_t:.2f}s] [Mote {m}] =================================================================")
        periodic_lines.append(f"[{boot_t+5.0:.2f}s] [Mote {m}] [NODE-{m}] Sensing loop active. Ready to transmit.")

    p_state = {}
    for m in range(2, 9):
        p_state[m] = {
            'seq': 0,
            'curr_temp': 2400 + (m * 35),
            'curr_humid': 5500 - (m * 50),
            'curr_light': 350 + (m * 20),
            'curr_co2': 400 + (m * 15),
            'transmitted': 0,
            'received': 0,
            'lost': 0,
            'battery': 3000,
            'cpu': 15000,
            'lpm': 32768 * 5,
            'tx': 500,
            'rx': 2500,
            'hop': 1 if m in [2, 3] else (2 if m in [4, 5, 6] else 3)
        }

    for t in range(10, 301, 5):
        for m in range(2, 9):
            st = p_state[m]
            st['seq'] += 1
            st['transmitted'] += 1
            st['cpu'] += random.randint(900, 1600)
            st['lpm'] += int(32768 * 4.8)
            # Periodic mode spends much more time transmitting and listening for ACK
            st['tx'] += random.randint(450, 580)
            st['rx'] += random.randint(1800, 2600)

            cycle = (t % 180) - 90
            noise = random.randint(-10, 10)
            st['curr_temp'] = (2400 + (m * 35)) + (cycle * 2) + noise
            st['curr_humid'] = (5500 - (m * 50)) - cycle + (noise * 2)
            st['curr_light'] = (350 + (m * 20)) + (cycle * 4) + noise
            st['curr_co2'] = (400 + (m * 15)) + (noise // 2)

            if m == 4 and 120 <= t <= 260:
                st['curr_temp'] += 2250
                st['curr_co2'] += 880

            if st['transmitted'] % 6 == 0:
                st['battery'] -= 1

            tx_t = t + (m * 0.12)
            periodic_lines.append(f"[{tx_t:.2f}s] [Mote {m}] [TX] Node={m} Seq={st['seq']} Type=DATA Temp={st['curr_temp']/100:.2f}C Humid={st['curr_humid']/100:.2f}% Light={st['curr_light']} CO2={st['curr_co2']} Batt={st['battery']}mV Suppressed=0")

            # In periodic mode, collisions occur at 2-hop and 3-hop distances
            loss_chance = 0.0 if st['hop'] == 1 else (0.05 if st['hop'] == 2 else 0.11)
            is_lost = (random.random() < loss_chance)

            rx_t = tx_t + (0.015 * st['hop'])
            if not is_lost:
                st['received'] += 1
                periodic_lines.append(f"[{rx_t:.2f}s] [Mote 1] [SINK-DATA] Time={int(rx_t)} Node={m} Seq={st['seq']} Type=NORMAL Temp={st['curr_temp']/100:.2f}C Humid={st['curr_humid']/100:.2f}% Light={st['curr_light']}lux CO2={st['curr_co2']}ppm Batt={st['battery']}mV Hops={st['hop']} Energest[CPU={st['cpu']} LPM={st['lpm']} TX={st['tx']} RX={st['rx']}]")
            else:
                st['lost'] += 1

            if st['transmitted'] % 12 == 0:
                eff_t = t + (m * 0.08)
                e_cpu = (3.0 * 0.0018 * st['cpu']) / 32768.0 * 1000.0
                e_lpm = (3.0 * 0.000055 * st['lpm']) / 32768.0 * 1000.0
                e_tx  = (3.0 * 0.0174 * st['tx']) / 32768.0 * 1000.0
                e_rx  = (3.0 * 0.0188 * st['rx']) / 32768.0 * 1000.0
                e_tot = e_cpu + e_lpm + e_tx + e_rx
                periodic_lines.append(f"[{eff_t:.2f}s] [Mote {m}] [ENERGY-MOTE-{m}] Total_mJ={e_tot:.2f} (CPU={e_cpu:.2f}, LPM={e_lpm:.2f}, TX={e_tx:.2f}, RX={e_rx:.2f})")
                periodic_lines.append(f"[{eff_t+0.01:.2f}s] [Mote {m}] [MOTE-{m}-EFFICIENCY] Samples={st['transmitted']} Transmitted={st['transmitted']} Suppressed=0 RadioSaving=0.0%")

        if t % 60 == 0:
            periodic_lines.append(f"[{t+0.9:.2f}s] [Mote 1] --- [NETWORK-SUMMARY @ {t} s] ---")
            periodic_lines.append(f"[{t+0.91:.2f}s] [Mote 1] Total Nodes Registered: 7")
            tot_rx = sum(st['received'] for st in p_state.values())
            tot_exp = sum(st['transmitted'] for st in p_state.values())
            g_pdr = (tot_rx / tot_exp) * 100.0 if tot_exp > 0 else 100.0
            periodic_lines.append(f"[{t+0.92:.2f}s] [Mote 1] Total Packets Received: {tot_rx} | Total Expected: {tot_exp} | Global PDR: {g_pdr:.2f}%")
            for m in range(2, 9):
                st = p_state[m]
                m_pdr = (st['received'] / st['transmitted']) * 100.0 if st['transmitted'] > 0 else 100.0
                periodic_lines.append(f"[{t+0.93+(m*0.01):.2f}s] [Mote 1]   Node {m:2d}: PktsRecv={st['received']:<4d} Lost={st['lost']:<3d} PDR={m_pdr:.1f}% LastSeen={t-int(t):<4d}s Temp={st['curr_temp']/100:2.2f}C Batt={st['battery']:4d}mV")
            periodic_lines.append(f"[{t+0.99:.2f}s] [Mote 1] ------------------------------------")

    periodic_lines.append("[300.00s] [Mote 1] =================================================================")
    periodic_lines.append("[300.00s] [Mote 1]   SIMULATION COMPLETED SUCCESSFULLY (5 Simulated Minutes)        ")
    periodic_lines.append("[300.00s] [Mote 1] =================================================================")

    with open("analysis/sample_data/cooja_adaptive_simulation.log", "w", encoding="utf-8") as f:
        f.write("\n".join(adaptive_lines) + "\n")

    with open("analysis/sample_data/cooja_periodic_simulation.log", "w", encoding="utf-8") as f:
        f.write("\n".join(periodic_lines) + "\n")

    print("[+] Successfully generated:")
    print("    - analysis/sample_data/cooja_adaptive_simulation.log")
    print("    - analysis/sample_data/cooja_periodic_simulation.log")

if __name__ == "__main__":
    generate_logs()
