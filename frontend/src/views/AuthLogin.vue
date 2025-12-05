<!-- src/views/AuthLogin.vue -->
<template>
  <div class="auth-screen d-flex align-items-center justify-content-center">
    <div class="row auth-card shadow-lg">
      <div class="col-md-6 auth-visual d-none d-md-flex flex-column justify-content-between">
        <div>
          <h2 class="mb-2">Find a spot, fast.</h2>
          <p class="mb-4">
            ParkFlow lets you manage city parking lots, monitor occupancy,
            and reserve spots without circling around.
          </p>
        </div>
        <div class="small" style="opacity:0.8;">
          Vehicle Parking App · MAD II
        </div>
      </div>

      <div class="col-md-6 auth-form-wrapper">
        <h3 class="mb-3">Sign in</h3>
        <p class=small style="opacity:0.8;">
          Use your account to access the parking dashboard.
          Admins sign in with their admin credentials.
        </p>

        <div class="mb-3">
          <label class="form-label">Username</label>
          <input
            v-model="username"
            type="text"
            class="form-control form-control-sm"
            placeholder="e.g. muskan_21"
          />
        </div>

        <div class="mb-3">
          <label class="form-label">Password</label>
          <input
            v-model="password"
            type="password"
            class="form-control form-control-sm"
            placeholder="Your secret password"
          />
        </div>

        <button class="btn btn-primary w-100 mb-2" :disabled="loading" @click="login">
          <span v-if="!loading">Continue</span>
          <span v-else>Signing you in...</span>
        </button>

        <p v-if="error" class="text-danger small mt-1">{{ error }}</p>

        <p class="small mt-3">
          New driver?
          <router-link to="/register">Create a parking account</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../api/axios";

export default {
  name: "AuthLogin",
  data() {
    return {
      username: "",
      password: "",
      loading: false,
      error: "",
    };
  },
  methods: {
    async login() {
      this.error = "";
      if (!this.username || !this.password) {
        this.error = "Please enter username and password.";
        return;
      }

      this.loading = true;
      try {
        const res = await api.post("/auth/login", {
          username: this.username,
          password: this.password,
        });

        const role = res.data.role;
        if (role === "admin") {
          this.$router.push("/admin");
        } else if (role === "user") {
          this.$router.push("/user");
        } else {
          this.error = "Unknown role. Contact admin.";
        }
      } catch (err) {
        this.error = err?.response?.data?.error || "Login failed.";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.auth-screen {
  min-height: 100vh;
  background: radial-gradient(circle at top, #041b2e 0, #02040a 60%, #000 100%);
  padding: 1.5rem;
}

.auth-card {
  max-width: 880px;
  width: 100%;
  border-radius: 18px;
  overflow: hidden;
  background: #050814;
}

.auth-visual {
  padding: 2.2rem 2rem;
  background: radial-gradient(circle at top left, #1dd1a1 0, #0652dd 50%, #000 100%);
  color: #f5f7ff;
}

.auth-form-wrapper {
  padding: 2.2rem 2rem;
  background: #050814;
  color: #f5f7ff;
}

.form-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.form-control {
  background: #070c1d;
  border-color: #1b2842;
  color: #f5f7ff !important;
}

.form-control::placeholder {
  color: rgba(245, 247, 255, 0.55);
}

.form-control:focus {
  background: #070c1d;
  border-color: #54a0ff;
  box-shadow: none;
}

.btn-primary {
  background: linear-gradient(135deg, #1dd1a1, #54a0ff);
  border: none;
}
</style>
