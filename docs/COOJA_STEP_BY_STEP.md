# Step-by-Step Cooja Network Simulation Tutorial

This guide walks you through compiling, running, and visualizing the **Smart Environmental Monitoring and Energy-Efficient WSN** project directly within the **Cooja Network Simulator**.

---

## 1. Prerequisites & Environments

You can run Cooja using any of the following setups:
1. **Instant Contiki 2.7 / 3.0 Virtual Machine** (VirtualBox or VMware)
2. **Ubuntu / Debian Native or WSL2** (Windows Subsystem for Linux)
3. **Docker Container** (Included in `docker/`)

### Required Packages:
```bash
sudo apt-get update
sudo apt-get install -y gcc-msp430 msp430-libc default-jdk ant build-essential
```

---

## 2. Compiling the Mote Firmware

Before loading into Cooja, ensure the TelosB firmware builds cleanly:

```bash
cd contiki-ng-app

# Clean previous build artifacts
make TARGET=sky clean

# Build the RPL Root Sink Firmware
make TARGET=sky sink-node.sky

# Build the Smart Environmental Sensor Firmware (Adaptive Mode)
make TARGET=sky sensor-node.sky

# (Optional) Build Fixed Periodic Baseline for comparison
make TARGET=sky ADAPTIVE=0 sensor-node.sky
```

---

## 3. Launching Cooja GUI

```bash
cd /path/to/contiki-ng/tools/cooja
ant run
```

---

## 4. Opening the Simulation Configuration

1. In Cooja, click **File** -> **Open simulation** -> **Browse...**
2. Navigate to your project directory:
   `cooja-simulations/smart_env_monitoring_8nodes.csc`
3. Click **Open**.

Cooja will load:
- **Simulation Control Panel**: Start, Pause, Step, Simulation Speed slider.
- **Network Visualizer**: 1 Sink Mote (Mote 1) + 7 Sensor Motes arranged in multi-hop topology.
- **Log Listener**: Real-time console logs from all motes with color-coded mote IDs.
- **Timeline**: Radio TX/RX states, LEDs, and microcontroller states.
- **Simulation Script**: Automated test runner configured in `simulation_script.js`.

---

## 5. Configuring Cooja Visualizer Plugins

To inspect network behavior visually:
1. In the **Network** window, click **View**:
   - Check **Mote IDs**
   - Check **Radio Traffic** (Draws green broadcast and blue unicast arrows during transmission)
   - Check **Node Attributes** (Shows hop distance and position)
   - Check **10m / 20m Grid**
   - Select **UDGM (Unit Disk Graph Medium)** radio coverage circles

---

## 6. Running the Simulation

1. Click **Start** in the Simulation Control panel.
2. Observe:
   - **Bootup Phase (0s - 15s)**: Sink initializes as RPL DAG root (`fd00::/64`). Motes discover the DODAG and establish routing paths.
   - **Stable Monitoring Phase (15s - 120s)**: Motes sample temperature (~25°C), humidity (~55%), light, and CO2. Notice that transmissions are suppressed when readings are stable!
   - **Anomaly Event Phase (120s - 260s)**: Mote 4 experiences an intense thermal surge (>45°C) and CO2 spike. The red LED flashes, and Mote 4 transmits immediate `[SINK-ALERT]` packets without delay.
   - **Sink Health Summary (Every 60s)**: The sink logs overall packet delivery ratio and active node counts.

---

## 7. Extracting and Analyzing Data

When the simulation finishes (or when paused):
1. In the **Log Listener** window, click **File** -> **Save to file...**
2. Save the log to: `analysis/sample_data/my_cooja_run.log`
3. Run the automated analysis suite:
```bash
python analysis/analyze_results.py analysis/sample_data/my_cooja_run.log
python analysis/generate_charts.py
```
4. View your results in `analysis/output/` and launch the dashboard:
```bash
python dashboard/run_dashboard.py
```
