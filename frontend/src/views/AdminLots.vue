<!-- src/views/AdminLots.vue -->
<template>
  <AppShell :username="user?.username" :role="user?.role" @logout="logout">

    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <button
          class="btn btn-outline-light btn-sm mb-2"
          @click="$router.push('/admin')"
        >
          ← Back to dashboard
        </button>

        <h5 class="mb-1">Parking lot configuration</h5>
        <p class="text-light small mb-0" style="opacity:0.7">
          Create, update or remove lots.
          Spots are generated automatically when a lot is created.
        </p>
      </div>

      <button class="btn btn-outline-light btn-sm" @click="loadLots">
        Refresh
      </button>
    </div>

    <!-- Body -->
    <div class="row g-3 mb-4">

      <!-- Add Lot -->
      <div class="col-md-5">
        <div class="panel">
          <h6 class="mb-3">Add new lot</h6>

          <div class="mb-2">
            <label class="form-label">Name</label>
            <input v-model="form.name" type="text" class="form-control form-control-sm" placeholder="e.g. City Mall Basement" />
          </div>

          <div class="mb-2">
            <label class="form-label">Address</label>
            <input v-model="form.address" type="text" class="form-control form-control-sm" placeholder="Optional address" />
          </div>

          <div class="row">
            <div class="col-6 mb-2">
              <label class="form-label">Pin code</label>
              <input v-model="form.pin_code" type="text" class="form-control form-control-sm" placeholder="e.g. 110001" />
            </div>
            <div class="col-6 mb-2">
              <label class="form-label">Price / hour</label>
              <input v-model="form.price_per_hour" type="number" min="0" class="form-control form-control-sm" placeholder="e.g. 40" />
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">Number of spots</label>
            <input v-model="form.number_of_spots" type="number" min="1" class="form-control form-control-sm" placeholder="e.g. 50" />
          </div>

          <button class="btn btn-success w-100 btn-sm" :disabled="saving" @click="createLot">
            <span v-if="!saving">Create lot</span>
            <span v-else>Creating...</span>
          </button>

          <p v-if="error" class="text-danger small mt-2">{{ error }}</p>
          <p v-if="message" class="text-success small mt-2">{{ message }}</p>
        </div>
      </div>

      <!-- Existing lots -->
      <div class="col-md-7">
        <div class="panel">
          <h6 class="mb-2">Existing lots</h6>

          <div class="table-responsive">
            <table class="table table-sm table-dark align-middle mb-0">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Price/hr</th>
                  <th>Spots</th>
                  <th>Active</th>
                  <th style="width: 180px;">Actions</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="lot in lots" :key="lot.id">
                  <td>
                    <input v-model="lot.edit_name" class="form-control form-control-sm bg-dark text-light border-0" />
                  </td>

                  <td style="width: 80px;">
                    <input v-model.number="lot.edit_price" type="number" min="0"
                      class="form-control form-control-sm bg-dark text-light border-0" />
                  </td>

                  <td style="width: 90px;">
                    <input
                      v-model.number="lot.edit_spots"
                      type="number"
                      min="1"
                      class="form-control form-control-sm bg-dark text-light border-0"
                    />
                  </td>

                  <td>
                    <input type="checkbox" v-model="lot.edit_active" class="form-check-input" />
                  </td>

                  <td>
                    <div class="d-flex gap-1">
                      <button class="btn btn-outline-light btn-xs" @click="openSpots(lot)">
                        Spots
                      </button>
                      <button class="btn btn-outline-success btn-xs" @click="saveLot(lot)">
                        Save
                      </button>
                      <button class="btn btn-outline-danger btn-xs" @click="removeLot(lot)">
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>

                <tr v-if="!lots.length">
                  <td colspan="5" class="text-center text-muted small">No lots yet.</td>
                </tr>

              </tbody>
            </table>
          </div>
        </div>

        <!-- Spot viewer -->
        <div v-if="selectedLot" class="panel mt-3">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">Spots in {{ selectedLot.prime_location_name }}</h6>
            <button class="btn btn-outline-light btn-xs" @click="selectedLot = null">Close</button>
          </div>

          <div class="table-responsive" v-if="spots.length">
            <table class="table table-sm table-dark align-middle mb-0">
              <thead>
                <tr>
                  <th>Spot</th>
                  <th>Status</th>
                  <th>User</th>
                  <th>Start time</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="s in spots" :key="s.id">
                  <td>{{ s.spot_number }}</td>

                  <td>
                    <span :class="['badge', s.status === 'O' ? 'bg-danger' : 'bg-success']">
                      {{ s.status === 'O' ? 'Occupied' : 'Available' }}
                    </span>
                  </td>

                  <td>{{ s.username || '-' }}</td>
                  <td class="small">
                    {{ s.start_time ? new Date(s.start_time).toLocaleString() : '-' }}
                  </td>

                </tr>
              </tbody>

            </table>
          </div>

          <p v-else class="text-muted small mb-0">No spots found.</p>
        </div>
      </div>
    </div>

  </AppShell>
</template>

<script>
import AppShell from "../components/AppShell.vue";
import api from "../api/axios";

export default {
  name: "AdminLots",
  components: { AppShell },

  data() {
    return {
      user: null,
      lots: [],
      spots: [],
      selectedLot: null,
      form: {
        name: "",
        address: "",
        pin_code: "",
        price_per_hour: "",
        number_of_spots: "",
      },
      saving: false,
      error: "",
      message: "",
    };
  },

  methods: {
    async loadUser() {
      const res = await api.get("/auth/me");
      this.user = res.data.user;
    },

    async loadLots() {
      const res = await api.get("/admin/parking-lots");
      this.lots = (res.data.lots || []).map((l) => ({
        ...l,
        edit_name: l.prime_location_name,
        edit_price: l.price_per_hour,
        edit_spots: l.number_of_spots,
        edit_active: l.is_active,
      }));
    },

    resetForm() {
      this.form = {
        name: "",
        address: "",
        pin_code: "",
        price_per_hour: "",
        number_of_spots: "",
      };
    },

    async createLot() {
      this.error = "";
      this.message = "";

      if (!this.form.name || !this.form.price_per_hour || !this.form.number_of_spots) {
        this.error = "Name, price and number of spots are required.";
        return;
      }

      this.saving = true;

      try {
        await api.post("/admin/parking-lots", {
          prime_location_name: this.form.name,
          address: this.form.address,
          pin_code: this.form.pin_code,
          price_per_hour: this.form.price_per_hour,
          number_of_spots: this.form.number_of_spots,
        });

        this.message = "Lot created.";
        this.resetForm();
        await this.loadLots();

      } catch (err) {
        this.error = err?.response?.data?.error || "Could not create lot.";
      } finally {
        this.saving = false;
      }
    },

    async saveLot(lot) {
      try {
        await api.put(`/admin/parking-lots/${lot.id}`, {
          prime_location_name: lot.edit_name,
          price_per_hour: lot.edit_price,
          is_active: lot.edit_active,
          number_of_spots: lot.edit_spots,
        });

        await this.loadLots();

      } catch (err) {
        alert(err?.response?.data?.error || "Could not update lot.");
      }
    },

    async removeLot(lot) {
      if (!confirm("Delete this lot? This action cannot be undone.")) return;

      try {
        await api.delete(`/admin/parking-lots/${lot.id}`);

        if (this.selectedLot?.id === lot.id) {
          this.selectedLot = null;
          this.spots = [];
        }

        await this.loadLots();

      } catch (err) {
        alert(err?.response?.data?.error || "Could not delete lot.");
      }
    },

    async openSpots(lot) {
      this.selectedLot = lot;
      const res = await api.get(`/admin/parking-lots/${lot.id}/spots`);
      this.spots = res.data.spots || [];
    },

    async logout() {
      await api.post("/auth/logout");
      this.$router.push("/login");
    },
  },

  async mounted() {
    await this.loadUser();

    if (!this.user || this.user.role !== "admin") {
      this.$router.push("/user");
      return;
    }

    await this.loadLots();
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

.btn-xs {
  padding: 0.15rem 0.35rem;
  font-size: 0.7rem;
}
</style>