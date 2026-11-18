# Smart Environmental Monitoring & Energy-Efficient Data Collection in WSN

A complete, production-grade Wireless Sensor Network (WSN) implementation developed for the **Cooja Network Simulator** and **Contiki-NG / Contiki-OS**.

This project pairs multi-hop **RPL (IPv6/6LoWPAN)** mesh networking with an **adaptive delta-threshold reporting scheme** and **Energest hardware power accounting** to extend sensor network operational lifetime.

---

## Performance Summary

| Metric | Baseline Periodic Mode | Adaptive Scheme (This Project) | Improvement |
| :--- | :---: | :---: | :---: |
| **Total Energy Consumed** | 1,953.2 mJ | 844.7 mJ | **56.8% Energy Saved** |
| **Radio Transmissions** | 413 packets | 120 packets | **70.9% Radio Reduction** |
| **Packet Delivery Ratio (PDR)** | 93.7% | 100.0% | **+6.3% Reliability** |
| **Average Node Power Draw** | 0.93 mW | 0.40 mW | **~8.7 Years on 2x AA** |
| **Hazard / Anomaly Alert** | Periodic delay | Immediate Priority TX | **Zero-latency detection** |

---

## Repository Structure

```
cooja-smart-environmental-monitoring/
│
├── contiki-ng-app/               # Contiki C source firmware
│   ├── common-header.h           # Shared packet structures & sensor thresholds
│   ├── project-conf.h            # Network, RPL, and Energest configurations
│   ├── sink-node.c               # RPL DAG Root (Collector & diagnostics)
│   ├── sensor-node.c             # Environmental Sensor Mote (Adaptive logic)
│   └── Makefile                  # Build script for TelosB / Sky motes
│
├── cooja-simulations/            # Cooja simulation setups
│   ├── smart_env_monitoring_8nodes.csc   # 8-node multi-hop topology
│   ├── smart_env_monitoring_20nodes.csc  # 20-node large-scale field topology
│   └── scripts/
│       ├── simulation_script.js          # Automated simulation test runner
│       └── run_simulation_headless.sh    # Headless batch execution script
│
├── analysis/                     # Benchmark analysis & log evaluation
│   ├── analyze_results.py        # Log parser & Energest power calculator
│   ├── generate_charts.py        # Standalone vector SVG chart generator
│   ├── sample_data/              # Pre-recorded simulation logs
│   └── output/                   # Generated benchmark charts & metrics
│
├── dashboard/                    # Interactive web dashboard
│   ├── index.html                # Responsive UI with dark-mode aesthetic
│   ├── styles.css                # Glassmorphic dashboard styles
│   ├── app.js                    # Interactive 2D topology & live telemetry
│   └── run_dashboard.py          # Standalone lightweight local server
│
├── docker/                       # Containerized environment
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── docs/                         # Technical documentation
    ├── ARCHITECTURE.md           # Protocol stack & mathematical energy model
    ├── COOJA_STEP_BY_STEP.md     # Visual walkthrough for running in Cooja
    └── VIVA_EXAM_PREPARATION.md  # Viva voce & academic review Q&A
```

---

## Quick Start

### 1. View the Interactive Dashboard
To view live topology animations, real-time charts, and simulation metrics:

```bash
# Using Python Launcher on Windows or standard python3 on Linux/macOS
python dashboard/run_dashboard.py
```
Open [http://localhost:8080/dashboard/index.html](http://localhost:8080/dashboard/index.html) in your browser.

---

### 2. Run the Benchmark Analytics & Generate SVG Charts

```bash
# Parse simulation logs and calculate energy consumption
python analysis/analyze_results.py

# Generate SVG vector charts
python analysis/generate_charts.py
```

Generated charts in `analysis/output/`:
- `chart1_energy_comparison.svg`: Total Energy per Mote (Adaptive vs. Periodic)
- `chart2_energy_breakdown.svg`: Energest Subsystem Power (CPU, LPM, TX, RX)
- `chart3_environmental_telemetry.svg`: Temperature profiles & Wildfire Event
- `chart4_radio_suppression_pdr.svg`: Reliability (PDR) vs. Radio Suppression

---

### 3. Run in Cooja Simulator

#### Option A: Cooja Graphical Interface
1. Launch Cooja in Contiki:
   ```bash
   cd contiki-ng/tools/cooja && ant run
   ```
2. Open `cooja-simulations/smart_env_monitoring_8nodes.csc`.
3. Click **Start** to run the simulation.

#### Option B: Headless Execution
```bash
bash cooja-simulations/scripts/run_simulation_headless.sh
```

#### Option C: Docker (Cross-Platform)
```bash
docker compose -f docker/docker-compose.yml up
```

---

## Pushing to GitHub

To push this project to your GitHub account:

```bash
# 1. Add all project files
git add .

# 2. Commit the codebase
git commit -m "feat: smart environmental monitoring & energy-efficient WSN in Cooja"

# 3. Link your GitHub repository
git remote add origin https://github.com/<your-username>/<your-repo-name>.git

# 4. Push to main branch
git branch -M main
git push -u origin main
```
