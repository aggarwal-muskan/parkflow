<!-- src/views/AdminHome.vue -->
<template>
  <AppShell :username="user?.username" :role="user?.role" @logout="logout">

    <!-- METRIC CARDS -->
    <div class="row g-3 mb-4">
      <div class="col-md-3" v-for="card in cards" :key="card.label">
        <div class="metric-card">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value">{{ card.value }}</div>
        </div>
      </div>
    </div>

    <!-- NAV BUTTONS -->
    <div class="d-flex justify-content-end gap-2 mb-3">
      <button
        class="btn btn-outline-light btn-sm"
        @click="$router.push('/admin/lots')"
      >
        Manage lots
      </button>
      <button
        class="btn btn-outline-light btn-sm"
        @click="$router.push('/admin/users')"
      >
        View users
      </button>
    </div>

    <!-- PARKING LOT TABLE -->
    <h5 class="mb-3">Parking lots overview</h5>
    <div class="table-responsive mb-4">
      <table class="table table-sm table-dark align-middle mb-0">
        <thead>
          <tr>
            <th>Lot</th>
            <th>Address</th>
            <th>Price/hr</th>
            <th>Total</th>
            <th>Occupied</th>
            <th>Free</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lot in lots" :key="lot.id">
            <td>{{ lot.prime_location_name }}</td>
            <td>{{ lot.address }}</td>
            <td>₹ {{ lot.price_per_hour }}</td>
            <td>{{ lot.total_spots }}</td>
            <td>{{ lot.occupied_spots }}</td>
            <td>{{ lot.available_spots }}</td>
          </tr>
          <tr v-if="!lots.length">
            <td colspan="6" class="text-center text-muted small">
              No parking lots available. Create one using admin tools.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- SUMMARY CHARTS -->
    <h5 class="mt-4 mb-3">Parking Summary</h5>

    <div class="row">
      <div class="col-md-6">
        <div class="panel">
          <h6 class="mb-2">Occupied vs Available</h6>
          <canvas id="chartSpots"></canvas>
        </div>
      </div>

      <div class="col-md-6">
        <div class="panel">
          <h6 class="mb-2">Spots per Lot</h6>
          <canvas id="chartLots"></canvas>
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
  name: "AdminHome",
  components: { AppShell },
  data() {
    return {
      user: null,
      summary: {},
      cards: [
        { label: "Lots", value: 0 },
        { label: "Spots", value: 0 },
        { label: "Occupied", value: 0 },
        { label: "Available", value: 0 },
      ],
      lots: [],
      _chartSpots: null,
      _chartLots: null,
    };
  },

  methods: {
    async loadUser() {
      const res = await api.get("/auth/me");
      this.user = res.data.user;
    },

    async loadSummary() {
      const res = await api.get("/admin/dashboard-summary");
      const s = res.data;

      this.summary = s;

      this.cards[0].value = s.total_lots;
      this.cards[1].value = s.total_spots;
      this.cards[2].value = s.occupied_spots;
      this.cards[3].value = s.available_spots;
    },

    async loadLots() {
      const res = await api.get("/admin/parking-lots/summary");
      this.lots = res.data.lots || [];
    },

    async logout() {
      await api.post("/auth/logout");
      this.$router.push("/login");
    },

    /* ------------------------------
     * Chart 1: Occupied vs Available
     * ------------------------------ */
    drawSpotSummary() {
      const ctx = document.getElementById("chartSpots");
      if (!ctx) return;

      if (this._chartSpots) this._chartSpots.destroy();

      this._chartSpots = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: ["Occupied", "Available"],
          datasets: [
            {
              data: [
                this.summary.occupied_spots,
                this.summary.available_spots,
              ],
              backgroundColor: ["#ff5757", "#3ddc84"],
            },
          ],
        },
        options: {
          plugins: {
            legend: { labels: { color: "#f3f5ff" } },
          },
        },
      });
    },

    /* ------------------------------
     * Chart 2: Spots per Lot
     * ------------------------------ */
    drawLotsSummary() {
      const ctx = document.getElementById("chartLots");
      if (!ctx) return;

      if (this._chartLots) this._chartLots.destroy();

      const labels = this.lots.map((l) => l.prime_location_name);
      const data = this.lots.map((l) => l.total_spots);

      this._chartLots = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              data,
              backgroundColor: "#4e7bff",
            },
          ],
        },
        options: {
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: "#f3f5ff" } },
            y: { ticks: { color: "#f3f5ff" } },
          },
        },
      });
    },
  },

  async mounted() {
    await this.loadUser();
    if (!this.user || this.user.role !== "admin") {
    this.$router.push("/user");
    return;
  }
    await Promise.all([this.loadSummary(), this.loadLots()]);

    this.$nextTick(() => {
      this.drawSpotSummary();
      this.drawLotsSummary();
    });
  },
};
</script>

<style scoped>
.metric-card {
  border-radius: 14px;
  padding: 1rem;
  background: linear-gradient(135deg, #07172f, #020813);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.metric-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  opacity: 0.7;
}

.metric-value {
  font-size: 1.4rem;
  font-weight: 600;
}

.panel {
  border-radius: 16px;
  padding: 1rem;
  background: #050814;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
