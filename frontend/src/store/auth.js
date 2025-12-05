// src/store/auth.js
import { defineStore } from "pinia";
import api from "../api/axios";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    loading: false,
    error: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.user,
    isAdmin: (state) => state.user?.role === "admin",
    isUser: (state) => state.user?.role === "user",
  },

  actions: {
    async loadUser() {
      try {
        const res = await api.get("/auth/me");
        this.user = res.data.user;
      } catch (err) {
        this.user = null;
      }
    },

    async login(username, password) {
      this.loading = true;
      this.error = null;
      try {
        const res = await api.post("/auth/login", { username, password });

        // Set user directly instead of calling /me again
        this.user = {
          username: res.data.username,
          role: res.data.role,
        };

        return this.user;
      } catch (err) {
        this.error = err?.response?.data?.error || "Login failed";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      try {
        await api.post("/auth/logout");
      } finally {
        this.user = null;
      }
    },
  },
});
