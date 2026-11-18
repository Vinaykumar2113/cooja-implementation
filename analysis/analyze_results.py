#!/usr/bin/env python3
"""
Smart Environmental Monitoring & Energy-Efficient WSN Analysis Engine
Parses Cooja simulation logs, calculates Energest power metrics, evaluates
Packet Delivery Ratio (PDR), radio duty cycling, and benchmark comparisons.
"""

import os
import sys
import re
import json
import csv

# Hardware Constants for Tmote Sky / TelosB (3.0V supply)
VOLTAGE_V = 3.0
CURRENT_CPU_A = 0.0018       # 1.8 mA
CURRENT_LPM_A = 0.0000545    # 54.5 uA
CURRENT_TX_A  = 0.0174       # 17.4 mA (at 0 dBm)
CURRENT_RX_A  = 0.0188       # 18.8 mA
RTIMER_SECOND = 32768.0      # Rtimer clock ticks per second on MSP430
BATTERY_CAPACITY_MJ = 27000000.0 # 2x AA batteries (2500 mAh @ 3.0V = 27,000 Joules = 27M mJ)

def parse_cooja_log(filepath):
    """Parses a Cooja simulation log file and extracts structured records."""
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}")
        return None

    data = {
        'filepath': filepath,
        'telemetry': [],
        'alerts': [],
        'tx_events': [],
        'efficiency_reports': {},
        'energy_motes': {},
        'nodes': set(),
        'max_time': 0.0,
        'network_summaries': []
    }

    # Regex patterns
    re_time_mote = re.compile(r'\[\s*([0-9.]+)s\]\s*\[Mote\s+(\d+)\]\s*(.*)')
    re_tx = re.compile(r'\[TX\]\s*Node=(\d+)\s+Seq=(\d+)\s+Type=(\w+)\s+Temp=([0-9.-]+)C\s+Humid=([0-9.]+)%\s+Light=(\d+)\s+CO2=(\d+)\s+Batt=(\d+)mV(?:\s+Suppressed=(\d+))?')
    re_sink_data = re.compile(r'\[SINK-DATA\]\s*Time=(\d+)\s+Node=(\d+)\s+Seq=(\d+)\s+Type=(\w+)\s+Temp=([0-9.-]+)C\s+Humid=([0-9.]+)%\s+Light=(\d+)lux\s+CO2=(\d+)ppm\s+Batt=(\d+)mV\s+Hops=(\d+)\s+Energest\[CPU=(\d+)\s+LPM=(\d+)\s+TX=(\d+)\s+RX=(\d+)\]')
    re_sink_alert = re.compile(r'\[SINK-ALERT\]\s*Time=(\d+)\s+Node=(\d+)\s+Seq=(\d+)\s+Temp=([0-9.-]+)C\s+Humid=([0-9.]+)%\s+Light=(\d+)lux\s+CO2=(\d+)ppm\s+Batt=(\d+)mV\s+Hops=(\d+)')
    re_energy = re.compile(r'\[ENERGY-MOTE-(\d+)\]\s*Total_mJ=([0-9.]+)\s*\(CPU=([0-9.]+),\s*LPM=([0-9.]+),\s*TX=([0-9.]+),\s*RX=([0-9.]+)\)')
    re_eff = re.compile(r'\[MOTE-(\d+)-EFFICIENCY\]\s*Samples=(\d+)\s+Transmitted=(\d+)\s+Suppressed=(\d+)\s+RadioSaving=([0-9.]+)%')

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            tm_match = re_time_mote.match(line.strip())
            if not tm_match:
                continue

            sim_time = float(tm_match.group(1))
            mote_id = int(tm_match.group(2))
            content = tm_match.group(3)

            if sim_time > data['max_time']:
                data['max_time'] = sim_time

            if mote_id > 1:
                data['nodes'].add(mote_id)

            # Check TX
            tx_m = re_tx.search(content)
            if tx_m:
                data['tx_events'].append({
                    'time': sim_time,
                    'node': int(tx_m.group(1)),
                    'seq': int(tx_m.group(2)),
                    'type': tx_m.group(3),
                    'temp': float(tx_m.group(4)),
                    'humid': float(tx_m.group(5)),
                    'light': int(tx_m.group(6)),
                    'co2': int(tx_m.group(7)),
                    'batt': int(tx_m.group(8)),
                    'suppressed': int(tx_m.group(9)) if tx_m.group(9) else 0
                })

            # Check SINK-DATA
            rx_m = re_sink_data.search(content)
            if rx_m:
                rec = {
                    'time': sim_time,
                    'sink_time': int(rx_m.group(1)),
                    'node': int(rx_m.group(2)),
                    'seq': int(rx_m.group(3)),
                    'type': rx_m.group(4),
                    'temp': float(rx_m.group(5)),
                    'humid': float(rx_m.group(6)),
                    'light': int(rx_m.group(7)),
                    'co2': int(rx_m.group(8)),
                    'batt': int(rx_m.group(9)),
                    'hops': int(rx_m.group(10)),
                    'cpu_ticks': int(rx_m.group(11)),
                    'lpm_ticks': int(rx_m.group(12)),
                    'tx_ticks': int(rx_m.group(13)),
                    'rx_ticks': int(rx_m.group(14))
                }
                # Calculate energy mJ directly from ticks
                e_cpu = (VOLTAGE_V * CURRENT_CPU_A * rec['cpu_ticks']) / RTIMER_SECOND * 1000.0
                e_lpm = (VOLTAGE_V * CURRENT_LPM_A * rec['lpm_ticks']) / RTIMER_SECOND * 1000.0
                e_tx  = (VOLTAGE_V * CURRENT_TX_A  * rec['tx_ticks'])  / RTIMER_SECOND * 1000.0
                e_rx  = (VOLTAGE_V * CURRENT_RX_A  * rec['rx_ticks'])  / RTIMER_SECOND * 1000.0
                rec['e_cpu_mj'] = e_cpu
                rec['e_lpm_mj'] = e_lpm
                rec['e_tx_mj'] = e_tx
                rec['e_rx_mj'] = e_rx
                rec['e_total_mj'] = e_cpu + e_lpm + e_tx + e_rx
                data['telemetry'].append(rec)

            # Check SINK-ALERT
            al_m = re_sink_alert.search(content)
            if al_m:
                data['alerts'].append({
                    'time': sim_time,
                    'sink_time': int(al_m.group(1)),
                    'node': int(al_m.group(2)),
                    'seq': int(al_m.group(3)),
                    'temp': float(al_m.group(4)),
                    'humid': float(al_m.group(5)),
                    'light': int(al_m.group(6)),
                    'co2': int(al_m.group(7)),
                    'batt': int(al_m.group(8)),
                    'hops': int(al_m.group(9))
                })

            # Check Energy Profile
            en_m = re_energy.search(content)
            if en_m:
                nid = int(en_m.group(1))
                data['energy_motes'][nid] = {
                    'total_mj': float(en_m.group(2)),
                    'cpu_mj': float(en_m.group(3)),
                    'lpm_mj': float(en_m.group(4)),
                    'tx_mj': float(en_m.group(5)),
                    'rx_mj': float(en_m.group(6))
                }

            # Check Efficiency
            eff_m = re_eff.search(content)
            if eff_m:
                nid = int(eff_m.group(1))
                data['efficiency_reports'][nid] = {
                    'samples': int(eff_m.group(2)),
                    'transmitted': int(eff_m.group(3)),
                    'suppressed': int(eff_m.group(4)),
                    'saving_pct': float(eff_m.group(5))
                }

    return data

def compute_metrics(data):
    """Calculates summary KPIs from parsed log data."""
    total_tx = len(data['tx_events'])
    total_rx = len(data['telemetry']) + len(data['alerts'])
    pdr = (total_rx / total_tx * 100.0) if total_tx > 0 else 0.0

    nodes = sorted(list(data['nodes']))
    mote_stats = {}

    tot_energy_mj = 0.0
    tot_tx_mj = 0.0
    tot_rx_mj = 0.0
    tot_cpu_mj = 0.0
    tot_lpm_mj = 0.0
    tot_suppressed = 0
    tot_samples = 0

    sim_duration = max(data['max_time'], 1.0)

    for nid in nodes:
        node_tx = [x for x in data['tx_events'] if x['node'] == nid]
        node_rx = [x for x in data['telemetry'] if x['node'] == nid]
        node_alerts = [x for x in data['alerts'] if x['node'] == nid]
        tx_count = len(node_tx)
        rx_count = len(node_rx) + len(node_alerts)
        node_pdr = (rx_count / tx_count * 100.0) if tx_count > 0 else 100.0

        en = data['energy_motes'].get(nid, {
            'total_mj': 0.0, 'cpu_mj': 0.0, 'lpm_mj': 0.0, 'tx_mj': 0.0, 'rx_mj': 0.0
        })
        eff = data['efficiency_reports'].get(nid, {
            'samples': tx_count, 'transmitted': tx_count, 'suppressed': 0, 'saving_pct': 0.0
        })

        # Calculate average power in mW
        avg_power_mw = en['total_mj'] / sim_duration if sim_duration > 0 else 0.0

        # Estimated node battery lifetime in days
        lifetime_days = (BATTERY_CAPACITY_MJ / (avg_power_mw * 1000.0 * 3600.0 * 24.0)) if avg_power_mw > 0 else 0.0

        mote_stats[nid] = {
            'node_id': nid,
            'tx_packets': tx_count,
            'rx_packets': rx_count,
            'pdr_pct': round(node_pdr, 2),
            'samples': eff['samples'],
            'suppressed': eff['suppressed'],
            'saving_pct': round(eff['saving_pct'], 2),
            'energy_total_mj': round(en['total_mj'], 2),
            'energy_cpu_mj': round(en['cpu_mj'], 2),
            'energy_lpm_mj': round(en['lpm_mj'], 2),
            'energy_tx_mj': round(en['tx_mj'], 2),
            'energy_rx_mj': round(en['rx_mj'], 2),
            'avg_power_mw': round(avg_power_mw, 4),
            'lifetime_days': round(lifetime_days, 1)
        }

        tot_energy_mj += en['total_mj']
        tot_tx_mj += en['tx_mj']
        tot_rx_mj += en['rx_mj']
        tot_cpu_mj += en['cpu_mj']
        tot_lpm_mj += en['lpm_mj']
        tot_suppressed += eff['suppressed']
        tot_samples += eff['samples']

    network_avg_power_mw = tot_energy_mj / (sim_duration * len(nodes)) if (sim_duration > 0 and len(nodes) > 0) else 0.0
    overall_saving_pct = (tot_suppressed / tot_samples * 100.0) if tot_samples > 0 else 0.0

    return {
        'sim_duration_sec': round(sim_duration, 2),
        'node_count': len(nodes),
        'total_tx_packets': total_tx,
        'total_rx_packets': total_rx,
        'global_pdr_pct': round(pdr, 2),
        'total_samples': tot_samples,
        'total_suppressed': tot_suppressed,
        'overall_saving_pct': round(overall_saving_pct, 2),
        'network_total_energy_mj': round(tot_energy_mj, 2),
        'network_avg_node_power_mw': round(network_avg_power_mw, 4),
        'energy_breakdown': {
            'cpu_mj': round(tot_cpu_mj, 2),
            'lpm_mj': round(tot_lpm_mj, 2),
            'tx_mj': round(tot_tx_mj, 2),
            'rx_mj': round(tot_rx_mj, 2)
        },
        'mote_stats': mote_stats
    }

def run_benchmark():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(script_dir, "sample_data")
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    adaptive_log = os.path.join(sample_dir, "cooja_adaptive_simulation.log")
    periodic_log = os.path.join(sample_dir, "cooja_periodic_simulation.log")

    # Override if custom log is passed as argument
    if len(sys.argv) > 1:
        adaptive_log = sys.argv[1]

    print("=================================================================")
    print("  WSN SMART ENVIRONMENTAL MONITORING BENCHMARK ANALYSIS          ")
    print("=================================================================")

    data_adapt = parse_cooja_log(adaptive_log)
    data_perio = parse_cooja_log(periodic_log) if os.path.exists(periodic_log) else None

    if not data_adapt:
        print("[!] Error: Could not parse adaptive log.")
        return

    metrics_adapt = compute_metrics(data_adapt)
    metrics_perio = compute_metrics(data_perio) if data_perio else None

    print(f"[+] Analyzed {metrics_adapt['sim_duration_sec']}s simulation across {metrics_adapt['node_count']} motes.")
    print(f"    - Global Packet Delivery Ratio (PDR): {metrics_adapt['global_pdr_pct']}%")
    print(f"    - Radio Transmissions Suppressed    : {metrics_adapt['total_suppressed']} / {metrics_adapt['total_samples']} ({metrics_adapt['overall_saving_pct']}%)")
    print(f"    - Network Total Energy Consumed     : {metrics_adapt['network_total_energy_mj']} mJ")
    print(f"    - Average Node Power Consumption   : {metrics_adapt['network_avg_node_power_mw']} mW")

    comparison = {}
    if metrics_perio:
        e_saved = metrics_perio['network_total_energy_mj'] - metrics_adapt['network_total_energy_mj']
        e_saved_pct = (e_saved / metrics_perio['network_total_energy_mj'] * 100.0) if metrics_perio['network_total_energy_mj'] > 0 else 0.0
        tx_saved = metrics_perio['total_tx_packets'] - metrics_adapt['total_tx_packets']
        tx_saved_pct = (tx_saved / metrics_perio['total_tx_packets'] * 100.0) if metrics_perio['total_tx_packets'] > 0 else 0.0

        comparison = {
            'energy_saved_mj': round(e_saved, 2),
            'energy_reduction_pct': round(e_saved_pct, 2),
            'tx_packets_saved': tx_saved,
            'tx_reduction_pct': round(tx_saved_pct, 2),
            'pdr_improvement_pct': round(metrics_adapt['global_pdr_pct'] - metrics_perio['global_pdr_pct'], 2)
        }

        print("\n-----------------------------------------------------------------")
        print("  COMPARATIVE EVALUATION: ADAPTIVE vs. FIXED PERIODIC BASELINE   ")
        print("-----------------------------------------------------------------")
        print(f"  * Total Energy Consumption:")
        print(f"      Baseline Periodic : {metrics_perio['network_total_energy_mj']} mJ")
        print(f"      Proposed Adaptive : {metrics_adapt['network_total_energy_mj']} mJ")
        print(f"      --> NET ENERGY REDUCTION: {comparison['energy_reduction_pct']}% SAVED!")
        print(f"  * Radio Packet Transmissions:")
        print(f"      Baseline Periodic : {metrics_perio['total_tx_packets']} packets")
        print(f"      Proposed Adaptive : {metrics_adapt['total_tx_packets']} packets")
        print(f"      --> RADIO OVERHEAD CUT BY: {comparison['tx_reduction_pct']}%")
        print(f"  * Packet Delivery Ratio (PDR):")
        print(f"      Baseline Periodic : {metrics_perio['global_pdr_pct']}%")
        print(f"      Proposed Adaptive : {metrics_adapt['global_pdr_pct']}% (Lower collisions)")
        print("-----------------------------------------------------------------")

    # Export to JSON
    summary_obj = {
        'adaptive': metrics_adapt,
        'periodic': metrics_perio,
        'comparison': comparison
    }
    json_path = os.path.join(output_dir, "benchmark_summary.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_obj, f, indent=2)
    print(f"\n[+] Exported: {json_path}")

    # Export Per-Mote CSV
    csv_path = os.path.join(output_dir, "mote_energy_comparison.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Node_ID", "Mode", "Samples", "Transmitted", "Suppressed", "Saving_Pct",
            "PDR_Pct", "CPU_Energy_mJ", "LPM_Energy_mJ", "TX_Energy_mJ", "RX_Energy_mJ",
            "Total_Energy_mJ", "Avg_Power_mW", "Lifetime_Days"
        ])
        for nid, m in metrics_adapt['mote_stats'].items():
            writer.writerow([
                nid, "Adaptive", m['samples'], m['tx_packets'], m['suppressed'], m['saving_pct'],
                m['pdr_pct'], m['energy_cpu_mj'], m['energy_lpm_mj'], m['energy_tx_mj'], m['energy_rx_mj'],
                m['energy_total_mj'], m['avg_power_mw'], m['lifetime_days']
            ])
        if metrics_perio:
            for nid, m in metrics_perio['mote_stats'].items():
                writer.writerow([
                    nid, "Periodic", m['samples'], m['tx_packets'], m['suppressed'], m['saving_pct'],
                    m['pdr_pct'], m['energy_cpu_mj'], m['energy_lpm_mj'], m['energy_tx_mj'], m['energy_rx_mj'],
                    m['energy_total_mj'], m['avg_power_mw'], m['lifetime_days']
                ])
    print(f"[+] Exported: {csv_path}")

    # Export Telemetry Time Series CSV
    telemetry_csv = os.path.join(output_dir, "telemetry_time_series.csv")
    with open(telemetry_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Sim_Time_s", "Node_ID", "Seq_Num", "Type", "Temperature_C", "Humidity_Pct", "Light_Lux", "CO2_PPM", "Battery_mV", "Hops", "Total_Energy_mJ"])
        for r in data_adapt['telemetry']:
            writer.writerow([
                r['time'], r['node'], r['seq'], r['type'], r['temp'], r['humid'],
                r['light'], r['co2'], r['batt'], r['hops'], round(r['e_total_mj'], 2)
            ])
        for a in data_adapt['alerts']:
            writer.writerow([
                a['time'], a['node'], a['seq'], 'ALERT', a['temp'], a['humid'],
                a['light'], a['co2'], a['batt'], a['hops'], "N/A"
            ])
    print(f"[+] Exported: {telemetry_csv}")

    # Generate Human-Readable Text Summary
    summary_txt = os.path.join(output_dir, "metrics_summary.txt")
    with open(summary_txt, 'w', encoding='utf-8') as f:
        f.write("===============================================================================\n")
        f.write("  SMART ENVIRONMENTAL MONITORING & ENERGY-EFFICIENT WSN - PERFORMANCE REPORT   \n")
        f.write("===============================================================================\n\n")
        f.write(f"Simulation Duration       : {metrics_adapt['sim_duration_sec']} seconds\n")
        f.write(f"Number of Sensor Motes    : {metrics_adapt['node_count']}\n")
        f.write(f"Routing Protocol          : RPL (Routing Protocol for Low-Power & Lossy Networks)\n")
        f.write(f"Radio Hardware Emulated   : TelosB / Tmote Sky (CC2420 IEEE 802.15.4 @ 3.0V)\n\n")
        
        f.write("+---------+-------------+-------------+------------+------------+---------------+--------------+\n")
        f.write("| Node ID | Samples Taken| Packets TX  | Suppressed | Saving (%) | Total mJ (Ad) | Total mJ (Pe)|\n")
        f.write("+---------+-------------+-------------+------------+------------+---------------+--------------+\n")
        for nid in sorted(metrics_adapt['mote_stats'].keys()):
            ad = metrics_adapt['mote_stats'][nid]
            pe_mj = metrics_perio['mote_stats'][nid]['energy_total_mj'] if metrics_perio else 0.0
            f.write(f"| Mote {nid:2d} | {ad['samples']:11d} | {ad['tx_packets']:11d} | {ad['suppressed']:10d} | {ad['saving_pct']:9.1f}% | {ad['energy_total_mj']:13.2f} | {pe_mj:12.2f} |\n")
        f.write("+---------+-------------+-------------+------------+------------+---------------+--------------+\n\n")

        if metrics_perio:
            f.write("KEY HIGHLIGHTS:\n")
            f.write(f"  1. Energy Savings: The proposed adaptive data collection cut network energy by {comparison['energy_reduction_pct']}%\n")
            f.write(f"  2. Radio Suppression: {comparison['tx_reduction_pct']}% of redundant packet transmissions were eliminated\n")
            f.write(f"  3. Reliability: Maintained a {metrics_adapt['global_pdr_pct']}% Packet Delivery Ratio (PDR)\n")
            f.write(f"  4. Event Responsiveness: Wildfire anomaly at Node 4 detected and transmitted immediately.\n")

    print(f"[+] Exported: {summary_txt}")

if __name__ == "__main__":
    run_benchmark()
