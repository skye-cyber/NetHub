// Connection timer
let startTime = Date.now();
function updateConnectionTime() {
  const elapsed = Date.now() - startTime;
  const minutes = Math.floor(elapsed / 60000);
  const seconds = Math.floor((elapsed % 60000) / 1000);
  document.getElementById("connectionTime").textContent =
    `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}
setInterval(updateConnectionTime, 1000);

// Bandwidth Chart
const bandwidthCtx = document.getElementById("bandwidthChart").getContext("2d");
const bandwidthChart = new Chart(bandwidthCtx, {
  type: "line",
  data: {
    labels: ["1m", "2m", "3m", "4m", "5m", "Now"],
    datasets: [
      {
        label: "Download (Mbps)",
        data: [0, 20, 45, 60, 75, 85],
        borderColor: "#667eea",
        backgroundColor: "rgba(102, 126, 234, 0.1)",
        tension: 0.4,
        fill: true,
      },
    ],
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
    },
  },
});

// Health Chart
const healthCtx = document.getElementById("healthChart").getContext("2d");
const healthChart = new Chart(healthCtx, {
  type: "doughnut",
  data: {
    labels: ["Signal", "Speed", "Latency", "Stability"],
    datasets: [
      {
        data: [95, 85, 90, 88],
        backgroundColor: ["#667eea", "#764ba2", "#f093fb", "#4fd1c7"],
      },
    ],
  },
  options: {
    responsive: true,
    cutout: "70%",
  },
});

// Interactive functions
function testConnection() {
  const speedElement = document.getElementById("connectionSpeed");
  speedElement.textContent = "Testing...";
  speedElement.style.color = "#e53e3e";

  setTimeout(() => {
    const speeds = [75, 80, 85, 90, 95];
    const randomSpeed = speeds[Math.floor(Math.random() * speeds.length)];
    speedElement.textContent = `${randomSpeed} Mbps`;
    speedElement.style.color = "#2d3748";

    // Show notification
    showNotification("Connection test completed successfully!");
  }, 2000);
}

function openSpeedTest() {
  window.open("https://fast.com", "_blank");
}

function showNetworkInfo() {
  const info = `Device Information:
IP Address: {{ client_ip }}
MAC Address: {{ client_mac }}
Connection Type: Secure WiFi
Gateway: 192.168.12.1`;
  alert(info);
}

function openHelp() {
  window.open("/help", "_blank");
}

function showNotification(message) {
  // Create notification element
  const notification = document.createElement("div");
  notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #48bb78;
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                z-index: 1000;
                animation: slideInRight 0.3s ease;
            `;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.remove();
  }, 3000);
}

// Simulate some dynamic updates
setInterval(() => {
  // Randomly update signal strength
  const strengths = ["Excellent", "Very Good", "Good"];
  document.getElementById("signalStrength").textContent =
    strengths[Math.floor(Math.random() * strengths.length)];
}, 5000);
