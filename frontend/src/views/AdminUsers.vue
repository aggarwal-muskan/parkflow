<!-- src/views/AdminUsers.vue -->
<template>
  <AppShell :username="user?.username" :role="user?.role" @logout="logout">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
            <button
            class="btn btn-outline-light btn-sm mb-2"
            @click="$router.push('/admin')"
            >
            ← Back to dashboard
            </button>
            <h5 class="mb-1">Registered users</h5>
            <p class="small" style="opacity:0.8;">
            View all accounts that can reserve parking spots.
            </p>
        </div>
        <button class="btn btn-outline-light btn-sm" @click="loadUsers">
            Refresh
        </button>
    </div>

    <div class="panel">
      <div class="table-responsive">
        <table class="table table-sm table-dark align-middle mb-0">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Role</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.username }}</td>
              <td>{{ u.email || '-' }}</td>
              <td>{{ u.phone || '-' }}</td>
              <td>{{ u.role }}</td>
              <td>
                <span
                  class="badge"
                  :class="u.is_active ? 'bg-success' : 'bg-secondary'"
                >
                  {{ u.is_active ? 'Active' : 'Disabled' }}
                </span>
              </td>
            </tr>
            <tr v-if="!users.length">
              <td colspan="5" class="text-center text-muted small">
                No users yet. Drivers can sign up from the registration page.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppShell>
</template>

<script>
import AppShell from "../components/AppShell.vue";
import api from "../api/axios";

export default {
  name: "AdminUsers",
  components: { AppShell },
  data() {
    return {
      user: null,
      users: [],
    };
  },
  methods: {
    async loadUser() {
      const res = await api.get("/auth/me");
      this.user = res.data.user;
    },
    async loadUsers() {
      const res = await api.get("/admin/users");
      this.users = res.data.users || [];
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
    await this.loadUsers();
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
