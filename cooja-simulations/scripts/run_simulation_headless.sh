#!/usr/bin/env bash
#
# Automated Headless Cooja Simulation Runner
# Runs the Cooja simulation without GUI and captures full logs for analysis.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP_DIR="${PROJECT_ROOT}/contiki-ng-app"
SIM_DIR="${PROJECT_ROOT}/cooja-simulations"
OUTPUT_DIR="${PROJECT_ROOT}/analysis/sample_data"

mkdir -p "${OUTPUT_DIR}"

# Locate Contiki root
if [ -z "${CONTIKI}" ]; then
  if [ -d "/home/user/contiki-ng" ]; then
    CONTIKI="/home/user/contiki-ng"
  elif [ -d "/home/user/contiki" ]; then
    CONTIKI="/home/user/contiki"
  elif [ -d "${PROJECT_ROOT}/../contiki-ng" ]; then
    CONTIKI="${PROJECT_ROOT}/../contiki-ng"
  else
    echo "[!] CONTIKI path not set. Please export CONTIKI=/path/to/contiki-ng"
    exit 1
  fi
fi

echo "================================================================="
echo "  HEADLESS COOJA SIMULATION AUTOMATION                           "
echo "  Contiki Path : ${CONTIKI}"
echo "  Project Root : ${PROJECT_ROOT}"
echo "================================================================="

# Step 1: Compile firmware binaries for TelosB / Sky target
echo "[1/3] Building Contiki firmware binaries for Sky motes..."
cd "${APP_DIR}"
make TARGET=sky clean
make TARGET=sky sink-node.sky sensor-node.sky

# Step 2: Run Headless Cooja Simulation
echo "[2/3] Launching Cooja headless simulation with 8-node topology..."
COOJA_JAR="${CONTIKI}/tools/cooja/dist/cooja.jar"
if [ ! -f "${COOJA_JAR}" ]; then
  COOJA_JAR="$(find ${CONTIKI} -name cooja.jar | head -n 1)"
fi

SIM_CSC="${SIM_DIR}/smart_env_monitoring_8nodes.csc"
LOG_FILE="${OUTPUT_DIR}/cooja_headless_run.log"

if [ -f "${COOJA_JAR}" ]; then
  java -mx512m -jar "${COOJA_JAR}" -nogui="${SIM_CSC}" -contiki="${CONTIKI}" | tee "${LOG_FILE}"
else
  echo "[*] Using ant run_nogui fallback..."
  cd "${CONTIKI}/tools/cooja"
  ant run_nogui -Dargs="${SIM_CSC}" | tee "${LOG_FILE}"
fi

# Step 3: Run Python post-processing and metric calculation
echo "[3/3] Parsing simulation log output and calculating metrics..."
cd "${PROJECT_ROOT}"
if command -v python3 &> /dev/null; then
  python3 analysis/analyze_results.py "${LOG_FILE}"
elif command -v py &> /dev/null; then
  py -3 analysis/analyze_results.py "${LOG_FILE}"
fi

echo "================================================================="
echo "  SIMULATION & ANALYSIS COMPLETE!                                "
echo "  Check results in analysis/output/ and launch dashboard/        "
echo "================================================================="
