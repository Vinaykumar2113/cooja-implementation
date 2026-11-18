/**
 * Smart Environmental Monitoring & Energy-Efficient WSN Dashboard Logic
 * Interactive 2D Network Topology, Real-time Canvas Charts & Telemetry Visualizer
 */

// Simulation and Network Configuration
const NETWORK_NODES = [
  { id: 1, type: "sink",   x: 320, y: 220, label: "Sink (DAG Root)",  parent: null, hops: 0, temp: 24.2, humid: 55.0, light: 380, co2: 410, batt: 3300, e_tot: 0,   status: "normal" },
  { id: 2, type: "sensor", x: 420, y: 170, label: "Mote 2 (Cluster 1)", parent: 1,    hops: 1, temp: 24.8, humid: 54.1, light: 395, co2: 430, batt: 2990, e_tot: 118, status: "normal" },
  { id: 3, type: "sensor", x: 220, y: 175, label: "Mote 3 (Cluster 2)", parent: 1,    hops: 1, temp: 25.1, humid: 53.6, light: 410, co2: 445, batt: 2991, e_tot: 119, status: "normal" },
  { id: 4, type: "sensor", x: 490, y: 110, label: "Mote 4 (Anomaly)",   parent: 2,    hops: 2, temp: 47.5, humid: 18.2, light: 850, co2: 1320, batt: 2975, e_tot: 134, status: "alert" },
  { id: 5, type: "sensor", x: 150, y: 120, label: "Mote 5 (Deep Field)",parent: 3,    hops: 2, temp: 25.7, humid: 52.4, light: 450, co2: 475, batt: 2988, e_tot: 121, status: "normal" },
  { id: 6, type: "sensor", x: 325, y: 110, label: "Mote 6 (Center)",    parent: 1,    hops: 1, temp: 26.1, humid: 51.9, light: 470, co2: 490, batt: 2989, e_tot: 120, status: "normal" },
  { id: 7, type: "sensor", x: 550, y: 50,  label: "Mote 7 (Perimeter)", parent: 4,    hops: 3, temp: 26.4, humid: 51.2, light: 490, co2: 505, batt: 2984, e_tot: 125, status: "normal" },
  { id: 8, type: "sensor", x: 90,  y: 60,  label: "Mote 8 (Perimeter)", parent: 5,    hops: 3, temp: 26.8, humid: 50.8, light: 510, co2: 520, batt: 2985, e_tot: 124, status: "normal" }
];

// Flying packet particles for animation
let packetParticles = [];

// ============================================================================
// 1. TOPOLOGY CANVAS ENGINE
// ============================================================================
function initTopologyCanvas() {
  const canvas = document.getElementById("topologyCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Resize canvas for sharp retina displays
  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  resize();
  window.addEventListener("resize", resize);

  // Periodic particle emission from sensor nodes towards their parents
  setInterval(() => {
    NETWORK_NODES.forEach(n => {
      if (n.parent !== null) {
        // Randomly emit telemetry packets along link
        if (Math.random() < (n.id === 4 ? 0.8 : 0.25)) {
          const parentNode = NETWORK_NODES.find(p => p.id === n.parent);
          if (parentNode) {
            packetParticles.push({
              fromX: n.x, fromY: n.y,
              toX: parentNode.x, toY: parentNode.y,
              progress: 0,
              speed: 0.015 + (Math.random() * 0.01),
              color: (n.id === 4 ? "#f38ba8" : "#89dceb")
            });
          }
        }
      }
    });
  }, 400);

  let pulseAngle = 0;

  function render() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;
    ctx.clearRect(0, 0, w, h);

    // Subtle background grid
    ctx.strokeStyle = "#252538";
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y < h; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Scale factors
    const scaleX = w / 640;
    const scaleY = h / 320;

    // Draw radio coverage circle for sink
    pulseAngle += 0.03;
    const sinkNode = NETWORK_NODES[0];
    const sinkX = sinkNode.x * scaleX;
    const sinkY = sinkNode.y * scaleY;
    const pulseRadius = 120 + Math.sin(pulseAngle) * 8;

    ctx.beginPath();
    ctx.arc(sinkX, sinkY, pulseRadius, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(137, 180, 250, 0.15)";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(sinkX, sinkY, pulseRadius * 0.65, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(137, 180, 250, 0.1)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // 1. Draw RPL Routing Edges
    NETWORK_NODES.forEach(n => {
      if (n.parent !== null) {
        const parent = NETWORK_NODES.find(p => p.id === n.parent);
        if (parent) {
          const nx = n.x * scaleX;
          const ny = n.y * scaleY;
          const px = parent.x * scaleX;
          const py = parent.y * scaleY;

          ctx.beginPath();
          ctx.moveTo(nx, ny);
          ctx.lineTo(px, py);
          ctx.strokeStyle = (n.id === 4) ? "rgba(243, 139, 168, 0.45)" : "rgba(137, 180, 250, 0.25)";
          ctx.lineWidth = (n.id === 4) ? 2.5 : 1.5;
          ctx.setLineDash([4, 4]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
    });

    // 2. Animate Flying Telemetry Packets
    for (let i = packetParticles.length - 1; i >= 0; i--) {
      const p = packetParticles[i];
      p.progress += p.speed;
      if (p.progress >= 1.0) {
        packetParticles.splice(i, 1);
        continue;
      }
      const curX = (p.fromX + (p.toX - p.fromX) * p.progress) * scaleX;
      const curY = (p.fromY + (p.toY - p.fromY) * p.progress) * scaleY;

      ctx.beginPath();
      ctx.arc(curX, curY, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0; // reset
    }

    // 3. Draw Mote Nodes
    NETWORK_NODES.forEach(n => {
      const nx = n.x * scaleX;
      const ny = n.y * scaleY;
      const isSink = (n.type === "sink");
      const isAlert = (n.status === "alert");

      let fillColor = isSink ? "#89b4fa" : (isAlert ? "#f38ba8" : "#a6e3a1");
      let nodeRadius = isSink ? 18 : 13;

      // Glow
      ctx.beginPath();
      ctx.arc(nx, ny, nodeRadius + 5, 0, Math.PI * 2);
      ctx.fillStyle = isAlert ? "rgba(243, 139, 168, 0.25)" : (isSink ? "rgba(137, 180, 250, 0.25)" : "rgba(166, 227, 161, 0.15)");
      ctx.fill();

      // Core Circle
      ctx.beginPath();
      ctx.arc(nx, ny, nodeRadius, 0, Math.PI * 2);
      ctx.fillStyle = fillColor;
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.8;
      ctx.stroke();

      // Label ID inside node
      ctx.fillStyle = "#11111b";
      ctx.font = "bold 11px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(isSink ? "SINK" : n.id, nx, ny);

      // Node Name & Temperature below node
      ctx.fillStyle = isAlert ? "#f38ba8" : "#cdd6f4";
      ctx.font = isAlert ? "bold 11px sans-serif" : "10px sans-serif";
      ctx.fillText(isSink ? "Sink (RPL Root)" : `Mote ${n.id} (${n.temp}°C)`, nx, ny + nodeRadius + 14);
    });

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);
}

// ============================================================================
// 2. TELEMETRY GRAPH CANVAS
// ============================================================================
function initTelemetryChart() {
  const canvas = document.getElementById("telemetryCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    drawChart();
  }
  resize();
  window.addEventListener("resize", resize);

  function drawChart() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;
    ctx.clearRect(0, 0, w, h);

    const padLeft = 50, padRight = 30, padTop = 30, padBottom = 40;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    // Grid lines for Temperature (20C to 50C)
    ctx.strokeStyle = "#252538";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#6c7086";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "right";

    const temps = [20, 25, 30, 35, 40, 45, 50];
    temps.forEach(t => {
      const y = padTop + plotH - ((t - 20) / 30) * plotH;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(padLeft + plotW, y);
      ctx.stroke();
      ctx.fillText(`${t}°C`, padLeft - 10, y + 4);
    });

    // Time marks (0s to 300s)
    ctx.textAlign = "center";
    for (let sec = 0; sec <= 300; sec += 50) {
      const x = padLeft + (sec / 300) * plotW;
      ctx.fillText(`${sec}s`, x, padTop + plotH + 20);
    }

    // Critical Alert Threshold Line (45C)
    const critY = padTop + plotH - ((45 - 20) / 30) * plotH;
    ctx.strokeStyle = "rgba(243, 139, 168, 0.7)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, critY);
    ctx.lineTo(padLeft + plotW, critY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#f38ba8";
    ctx.textAlign = "right";
    ctx.fillText("CRITICAL THRESHOLD (45°C)", padLeft + plotW, critY - 6);

    // Synthetic curves for normal motes (Motes 2, 3, 5, 6, 7, 8)
    const normalMotes = [2, 3, 5, 6, 7, 8];
    normalMotes.forEach(nid => {
      ctx.beginPath();
      ctx.strokeStyle = "rgba(137, 220, 235, 0.35)";
      ctx.lineWidth = 1.2;
      for (let sec = 0; sec <= 300; sec += 10) {
        const cycle = Math.sin(sec / 30 + nid) * 1.5;
        const temp = 24.5 + (nid * 0.35) + cycle;
        const px = padLeft + (sec / 300) * plotW;
        const py = padTop + plotH - ((temp - 20) / 30) * plotH;
        if (sec === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
    });

    // Anomaly Curve for Node 4 (Spikes from 26C to 47.8C between 120s and 260s)
    ctx.beginPath();
    ctx.strokeStyle = "#f38ba8";
    ctx.lineWidth = 2.8;
    for (let sec = 0; sec <= 300; sec += 5) {
      let temp = 25.5 + Math.sin(sec / 25) * 1.2;
      if (sec >= 120 && sec <= 260) {
        const progress = Math.sin(((sec - 120) / 140) * Math.PI);
        temp += progress * 22.0; // spikes up to 47.5C
      }
      const px = padLeft + (sec / 300) * plotW;
      const py = padTop + plotH - ((temp - 20) / 30) * plotH;
      if (sec === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // Peak Alert Marker
    const alertPeakX = padLeft + (190 / 300) * plotW;
    const alertPeakY = padTop + plotH - ((47.5 - 20) / 30) * plotH;
    ctx.beginPath();
    ctx.arc(alertPeakX, alertPeakY, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#f38ba8";
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = "#f38ba8";
    ctx.font = "bold 11px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Node 4 Wildfire Surge (47.5°C)", alertPeakX, alertPeakY - 12);
  }
}

// ============================================================================
// 3. POPULATE MOTE TABLE
// ============================================================================
function populateMoteTable() {
  const tbody = document.getElementById("moteTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";
  NETWORK_NODES.forEach(n => {
    const tr = document.createElement("tr");
    const isSink = (n.type === "sink");
    const isAlert = (n.status === "alert");

    const badgeClass = isSink ? "badge-sink" : (isAlert ? "badge-alert" : "badge-sensor");
    const roleText = isSink ? "RPL DAG Root" : `Sensor Node (Hops: ${n.hops})`;
    const statusText = isSink ? "LISTENING" : (isAlert ? "CRITICAL ALERT" : "MONITORING");

    tr.innerHTML = `
      <td><strong>${isSink ? "Mote 1 (Sink)" : `Mote ${n.id}`}</strong></td>
      <td><span class="badge ${badgeClass}">${roleText}</span></td>
      <td><span style="color: ${isAlert ? 'var(--accent-red)' : 'var(--text-main)'}; font-weight: bold;">${n.temp.toFixed(1)} °C</span></td>
      <td>${n.humid.toFixed(1)} %</td>
      <td>${n.light} Lux</td>
      <td>${n.co2} PPM</td>
      <td>${n.batt} mV</td>
      <td><span class="kpi-highlight-green">~70.8%</span></td>
      <td><strong>${isSink ? "0.00" : n.e_tot.toFixed(1)} mJ</strong></td>
      <td><span class="badge ${badgeClass}">${statusText}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// Initialization on DOM Load
document.addEventListener("DOMContentLoaded", () => {
  initTopologyCanvas();
  initTelemetryChart();
  populateMoteTable();
});
