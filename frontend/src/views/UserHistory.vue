<!-- src/views/UserHistory.vue -->
<template>
  <AppShell :username="user?.username" :role="user?.role" @logout="logout">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <button
          class="btn btn-outline-light btn-sm mb-2"
          @click="$router.push('/user')"
        >
          ← Back to parking
        </button>
        <h5 class="mb-1">Parking history</h5>
        <p class="small mb-0" style="opacity: 0.8;">
          All completed and active sessions linked to your account.
        </p>
      </div>

      <div class="text-end">
        <button
          class="btn btn-success btn-sm mb-2"
          :disabled="exporting"
          @click="exportCsv"
        >
          <span v-if="!exporting">Export as CSV</span>
          <span v-else>Preparing export...</span>
        </button>
        <p v-if="exportMessage" class="small mt-1 mb-0">
          {{ exportMessage }}
        </p>
      </div>
    </div>

    <!-- HISTORY TABLE -->
    <div class="panel mb-4">
      <div class="table-responsive">
        <table class="table table-sm table-dark align-middle mb-0">
          <thead>
            <tr>
              <th>#</th>
              <th>Lot</th>
              <th>Spot</th>
              <th>Start</th>
              <th>End</th>
              <th>Cost</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, index) in reservations" :key="r.id">
              <td>{{ index + 1 }}</td>
              <td>{{ r.lot_name }}</td>
              <td>{{ r.spot_number }}</td>
              <td class="small">{{ formatTime(r.parking_in) }}</td>
              <td class="small">{{ formatTime(r.parking_out) }}</td>
              <td>
                <span v-if="r.parking_cost != null">
                  ₹ {{ r.parking_cost.toFixed(2) }}
                </span>
                <span v-else>-</span>
              </td>
              <td>
                <span class="badge" :class="statusClass(r.status)">
                  {{ r.status }}
                </span>
              </td>
            </tr>

            <tr v-if="!reservations.length">
              <td colspan="7" class="text-center small" style="opacity: 0.8;">
                No reservations yet. Book a spot to see it here.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- USER CHARTS -->
    <h5 class="mt-4 mb-3">Your Parking Insights</h5>

    <div class="row">
      <div class="col-md-6">
        <div class="panel">
          <h6 class="mb-2">Cost per visit</h6>
          <canvas id="chartCost"></canvas>
        </div>
      </div>

      <div class="col-md-6">
        <div class="panel">
          <h6 class="mb-2">Most used parking lots</h6>
          <canvas id="chartLotsUsage"></canvas>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script>
import AppShell from "../components/AppShell.vue";
import api from "../api/axios";
import { Chart } from "chart.js/auto";

export default {
  name: "UserHistory",
  components: { AppShell },

  data() {
    return {
      user: null,
      reservations: [],
      exporting: false,
      exportMessage: "",
      _chartCost: null,
      _chartLotsUsage: null,
    };
  },

  methods: {
    async loadUser() {
      const res = await api.get("/auth/me");
      this.user = res.data.user;
    },

    async loadHistory() {
      const res = await api.get("/user/reservations/history");
      this.reservations = res.data.reservations || [];

      // rebuild charts after data loads
      this.$nextTick(() => {
        this.drawCostChart();
        this.drawLotUsageChart();
      });
    },

    statusClass(status) {
      if (status === "active") return "bg-info";
      if (status === "completed") return "bg-success";
      if (status === "cancelled") return "bg-secondary";
      return "bg-dark";
    },

    formatTime(ts) {
      if (!ts) return "-";
      try {
        const d = new Date(ts);
        return d.toLocaleString("en-IN", {
          year: "numeric",
          month: "short",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });
      } catch {
        return ts;
      }
    },

    async exportCsv() {
      this.exportMessage = "";
      this.exporting = true;
      try {
        const res = await api.post("/user/export-csv");
        const id = res.data.export_id;
        this.exportMessage = `Export request created (id: ${id}). The file will be prepared by the background job.`;
      } catch (err) {
        this.exportMessage =
          err?.response?.data?.error || "Could not start export.";
      } finally {
        this.exporting = false;
      }
    },

    logout() {
      api.post("/auth/logout");
      this.$router.push("/login");
    },

    // ---------- CHARTS ----------

    drawCostChart() {
      const ctx = document.getElementById("chartCost");
      if (!ctx) return;

      if (this._chartCost) {
        this._chartCost.destroy();
      }

      if (!this.reservations.length) {
        // no data chart
        this._chartCost = new Chart(ctx, {
          type: "bar",
          data: {
            labels: ["No data"],
            datasets: [
              {
                label: "₹ per visit",
                data: [0],
                backgroundColor: "#2c3340",
              },
            ],
          },
          options: {
            plugins: {
              legend: { labels: { color: "#f3f5ff" } },
            },
            scales: {
              x: { ticks: { color: "#f3f5ff" } },
              y: { ticks: { color: "#f3f5ff" } },
            },
          },
        });
        return;
      }

      const labels = this.reservations.map((r, idx) => {
        // show short date with an index
        const d = r.parking_in ? r.parking_in.slice(0, 10) : `Visit ${idx + 1}`;
        return d;
      });

      const data = this.reservations.map((r) => r.parking_cost || 0);

      this._chartCost = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              label: "₹ per visit",
              data,
              backgroundColor: "#6ee7ff",
            },
          ],
        },
        options: {
          plugins: {
            legend: {
              labels: { color: "#f3f5ff" },
            },
          },
          scales: {
            x: { ticks: { color: "#f3f5ff" } },
            y: { ticks: { color: "#f3f5ff" } },
          },
        },
      });
    },

    drawLotUsageChart() {
      const ctx = document.getElementById("chartLotsUsage");
      if (!ctx) return;

      if (this._chartLotsUsage) {
        this._chartLotsUsage.destroy();
      }

      if (!this.reservations.length) {
        this._chartLotsUsage = new Chart(ctx, {
          type: "doughnut",
          data: {
            labels: ["No data"],
            datasets: [
              {
                data: [1],
                backgroundColor: ["#2c3340"],
              },
            ],
          },
          options: {
            plugins: {
              legend: { labels: { color: "#f3f5ff" } },
            },
          },
        });
        return;
      }

      // Aggregate count by lot_name
      const usage = {};
      this.reservations.forEach((r) => {
        if (!r.lot_name) return;
        usage[r.lot_name] = (usage[r.lot_name] || 0) + 1;
      });

      const labels = Object.keys(usage);
      const values = Object.values(usage);

      if (!labels.length) {
        this._chartLotsUsage = new Chart(ctx, {
          type: "doughnut",
          data: {
            labels: ["No data"],
            datasets: [
              {
                data: [1],
                backgroundColor: ["#2c3340"],
              },
            ],
          },
          options: {
            plugins: {
              legend: { labels: { color: "#f3f5ff" } },
            },
          },
        });
        return;
      }

      this._chartLotsUsage = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: ["#ff5757", "#4e7bff", "#3ddc84", "#facc15"],
            },
          ],
        },
        options: {
          plugins: {
            legend: {
              labels: { color: "#f3f5ff" },
            },
          },
        },
      });
    },
  },

  async mounted() {
    await this.loadUser();

    // If somehow admin lands here, redirect to admin dashboard
    if (this.user && this.user.role === "admin") {
      this.$router.push("/admin");
      return;
    }

    await this.loadHistory();
  },
};
</script>

<style scoped>
.panel {
  border-radius: 16px;
  padding: 1rem;
  background: #050814;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
