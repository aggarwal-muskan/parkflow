<!-- src/views/AuthRegister.vue -->
<template>
  <div class="auth-screen d-flex align-items-center justify-content-center">
    <div class="auth-card-small shadow-lg">
      <h3 class="mb-3 text-center">Create driver account</h3>
      <p class="small" style="opacity:0.8; text-align: center;">
        This account is for regular users who want to reserve parking spots.
      </p>

      <div class="mb-3">
        <label class="form-label">Username</label>
        <input
          v-model="username"
          type="text"
          class="form-control form-control-sm"
          placeholder="Choose a username"
        />
      </div>

      <div class="mb-3">
        <label class="form-label">Email (optional)</label>
        <input
          v-model="email"
          type="email"
          class="form-control form-control-sm"
          placeholder="you@example.com"
        />
      </div>

      <div class="mb-3">
        <label class="form-label">Phone (optional)</label>
        <input
          v-model="phone"
          type="text"
          class="form-control form-control-sm"
          placeholder="Contact number"
        />
      </div>

      <div class="mb-3">
        <label class="form-label">Password</label>
        <input
          v-model="password"
          type="password"
          class="form-control form-control-sm"
          placeholder="At least 6 characters"
        />
      </div>

      <button class="btn btn-success w-100 mb-2" :disabled="loading" @click="register">
        <span v-if="!loading">Sign up</span>
        <span v-else>Creating account...</span>
      </button>

      <p v-if="error" class="text-danger small mt-1">{{ error }}</p>
      <p v-if="message" class="text-success small mt-1">{{ message }}</p>

      <p class="small mt-3 text-center">
        Already have access?
        <router-link to="/login">Sign in</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import api from "../api/axios";

export default {
  name: "AuthRegister",
  data() {
    return {
      username: "",
      email: "",
      phone: "",
      password: "",
      loading: false,
      error: "",
      message: "",
    };
  },
  methods: {
    async register() {
      this.error = "";
      this.message = "";

      if (!this.username || !this.password) {
        this.error = "Username and password are required.";
        return;
      }

      this.loading = true;
      try {
        const res = await api.post("/auth/register", {
          username: this.username,
          email: this.email,
          phone: this.phone,
          password: this.password,
        });

        this.message = res.data.message || "Account created.";
      } catch (err) {
        this.error = err?.response?.data?.error || "Could not create account.";
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
  background: radial-gradient(circle at bottom, #03101c 0, #02040a 60%, #000 100%);
  padding: 1.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.auth-card-small {
  max-width: 420px;
  width: 100%;
  border-radius: 18px;
  padding: 2rem;
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
  border-color: #1dd1a1;
  box-shadow: none;
}
</style>
