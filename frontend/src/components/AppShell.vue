<!-- src/components/AppShell.vue -->
<template>
  <div class="app-shell d-flex flex-column min-vh-100">
    <header class="app-header d-flex align-items-center justify-content-between px-4">
      <div class="d-flex align-items-center gap-2">
        <div class="brand-marker"></div>
        <div>
          <div class="brand-title">ParkFlow</div>
          <div class="brand-sub">Smart parking for busy places</div>
        </div>
      </div>

      <div class="d-flex align-items-center gap-3">
        <div v-if="username" class="text-end">
          <div class="user-role-label">{{ roleLabel }}</div>
          <div class="user-name-label">{{ username }}</div>
        </div>
        <button v-if="showLogout" class="btn btn-sm btn-outline-light" @click="$emit('logout')">
          Sign out
        </button>
      </div>
    </header>

    <main class="flex-fill app-main">
      <div class="container py-4">
        <slot></slot>
      </div>
    </main>

    <footer class="app-footer text-center py-2">
      <small>ParkFlow · Vehicle Parking System</small>
    </footer>
  </div>
</template>

<script>
export default {
  name: "AppShell",
  props: {
    username: String,
    role: String,
    showLogout: {
      type: Boolean,
      default: true,
    },
  },
  computed: {
    roleLabel() {
      if (this.role === "admin") return "Administrator";
      if (this.role === "user") return "Registered Driver";
      return "";
    },
  },
};
</script>

<style scoped>
.app-shell {
  background: radial-gradient(circle at top, #071b3b 0, #020715 55%, #000 100%);
  color: #f5f7ff;
}

.app-header {
  height: 64px;
  background: rgba(5, 12, 32, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.brand-marker {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: linear-gradient(135deg, #1dd1a1, #54a0ff);
}

.brand-title {
  font-weight: 600;
  font-size: 1rem;
}

.brand-sub {
  font-size: 0.75rem;
  opacity: 0.7;
}

.user-role-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.7;
}

.user-name-label {
  font-size: 0.9rem;
}

.app-main {
  background: radial-gradient(circle at bottom, #03101c 0, #02040a 50%, #000 100%);
}

.app-footer {
  font-size: 0.75rem;
  opacity: 0.7;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: #02040a;
}
</style>
