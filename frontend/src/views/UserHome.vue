<!-- src/views/UserHome.vue -->
<template>
  <AppShell :username="user?.username" :role="user?.role" @logout="logout">
    <!-- HEADER -->
    <div class="row mb-4">
      <div class="col-md-6">
        <h5 class="mb-2">Available parking lots</h5>
        <p class="text-muted small mb-0">
          Choose a lot and the system will assign the first free spot.
        </p>
      </div>

      <div class="col-md-6 text-md-end mt-3 mt-md-0">
        <button
          class="btn btn-outline-light btn-sm me-2"
          @click="$router.push('/user/history')"
        >
          View history
        </button>

        <button class="btn btn-outline-light btn-sm" @click="refresh">
          Refresh list
        </button>
      </div>
    </div>

    <!-- ACTIVE RESERVATION CARD -->
    <div v-if="active" class="active-card mb-4 p-3">
      <h6 class="mb-2">Your Active Parking</h6>

      <div class="d-flex justify-content-between align-items-start">
        <div>
          <div class="fw-bold">{{ active.lot_name }}</div>
          <div class="small text-muted">Spot #{{ active.spot_number }}</div>

          <div class="small mt-1">
            Started: {{ formatTime(active.parking_in) }}
          </div>

          <div class="mt-2 text-info">
            ⏱ Parked for: <strong>{{ liveTimer }}</strong>
          </div>
        </div>

        <div>
          <button
            class="btn btn-danger btn-sm"
            @click="endParking"
            :disabled="processingEnd"
          >
            <span v-if="!processingEnd">End Parking</span>
            <span v-else>Processing…</span>
          </button>
        </div>
      </div>
    </div>

    <!-- PARKING LOT CARDS -->
    <div class="row g-3 mb-4">
      <div class="col-md-4" v-for="lot in lots" :key="lot.id">
        <div class="lot-card h-100 d-flex flex-column">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
              <div class="lot-name">{{ lot.prime_location_name }}</div>
              <div class="lot-address small text-muted">
                {{ lot.address || "No address added" }}
              </div>
            </div>
            <div class="lot-price text-end">
              <div class="small text-muted">Price/hr</div>
              <div>₹ {{ lot.price_per_hour }}</div>
            </div>
          </div>

          <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="small">
              Total: {{ lot.total_spots }}<br />
              Occupied: {{ lot.occupied_spots }}
            </div>
            <div class="lot-free">
              Free: {{ lot.available_spots }}
            </div>
          </div>

          <button
            class="btn btn-success btn-sm w-100 mt-auto"
            :disabled="lot.available_spots <= 0 || booking"
            @click="book(lot.id)"
          >
            <span v-if="!booking">Reserve spot</span>
            <span v-else>Processing...</span>
          </button>
        </div>
      </div>

      <div v-if="!lots.length" class="col-12 text-center text-muted small">
        No lots available yet.
      </div>
    </div>
  </AppShell>
</template>

<script>
import AppShell from "../components/AppShell.vue";
import api from "../api/axios";

export default {
  name: "UserHome",
  components: { AppShell },
  data() {
    return {
      user: null,
      lots: [],
      active: null,
      booking: false,

      // Timer
      liveTimer: "0s",
      timerInterval: null,
      processingEnd: false,
    };
  },

  methods: {
    async loadUser() {
      const res = await api.get("/auth/me");
      this.user = res.data.user;
    },

    async loadLots() {
      const res = await api.get("/user/parking-lots");
      this.lots = res.data.lots || [];
    },

    async loadActive() {
      const res = await api.get("/user/reservations/current");
      this.active = res.data.reservation || null;

      if (this.active) {
        this.startTimer();
      } else {
        this.stopTimer();
        this.liveTimer = "0s";
      }
    },

    async refresh() {
      await Promise.all([this.loadLots(), this.loadActive()]);
    },

    async book(lotId) {
      this.booking = true;
      try {
        await api.post("/user/reservations", { lot_id: lotId });
        await this.refresh();
      } catch (err) {
        alert(err?.response?.data?.error || "Could not create reservation.");
      } finally {
        this.booking = false;
      }
    },

    async endParking() {
      if (!this.active) return;
      this.processingEnd = true;

      try {
        await api.put(`/user/reservations/${this.active.id}/release`);
        await this.refresh();
      } catch (err) {
        alert(err?.response?.data?.error || "Could not end reservation.");
      }

      this.processingEnd = false;
    },

    // Fix timer & timezone bug
    startTimer() {
      this.stopTimer();

      if (!this.active || !this.active.parking_in) {
        this.liveTimer = "0s";
        return;
      }

      const raw = this.active.parking_in;
      const start =
        raw.endsWith("Z") || raw.includes("+")
          ? new Date(raw) // already has timezone
          : new Date(raw + "Z"); // treat as UTC

      this.timerInterval = setInterval(() => {
        const now = new Date();
        const sec = Math.max(0, Math.floor((now - start) / 1000));

        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        const s = sec % 60;

        if (h > 0) this.liveTimer = `${h}h ${m}m ${s}s`;
        else if (m > 0) this.liveTimer = `${m}m ${s}s`;
        else this.liveTimer = `${s}s`;
      }, 1000);
    },

    stopTimer() {
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
      }
    },

    // Human readable date/time
    formatTime(ts) {
      if (!ts) return "-";

      const date = new Date(
        ts.endsWith("Z") || ts.includes("+") ? ts : ts + "Z"
      );

      return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "numeric",
        hour12: true,
      });
    },

    async logout() {
      await api.post("/auth/logout");
      this.$router.push("/login");
    },
  },

  async mounted() {
    await this.loadUser();
    if (this.user && this.user.role === "admin") {
    this.$router.push("/admin");
    return;
  }
    await this.refresh();
  },

  beforeUnmount() {
    this.stopTimer();
  },
};
</script>

<style scoped>
.lot-card {
  border-radius: 14px;
  padding: 1rem;
  background: linear-gradient(135deg, #0a1524, #050814);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.lot-name {
  font-weight: 600;
}

.lot-free {
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  background: rgba(29, 209, 161, 0.12);
  font-size: 0.8rem;
}

.active-card {
  border-radius: 16px;
  background: #070c1d;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.text-muted {
  color: rgba(255, 255, 255, 0.75) !important;
}
.small {
  color: rgba(255, 255, 255, 0.85);
}
td, th {
  color: #f3f5ff !important;
}

.badge {
  color: #fff;
}

</style>