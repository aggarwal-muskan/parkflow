import { createRouter, createWebHistory } from "vue-router";

import AuthLogin from "../views/AuthLogin.vue";
import AuthRegister from "../views/AuthRegister.vue";
import AdminHome from "../views/AdminHome.vue";
import UserHome from "../views/UserHome.vue";
import AdminLots from "../views/AdminLots.vue";
import AdminUsers from "../views/AdminUsers.vue";
import UserHistory from "../views/UserHistory.vue"; // 👈 add this

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", name: "AuthLogin", component: AuthLogin },
  { path: "/register", name: "AuthRegister", component: AuthRegister },

  { path: "/admin", name: "AdminHome", component: AdminHome },
  { path: "/admin/lots", name: "AdminLots", component: AdminLots },
  { path: "/admin/users", name: "AdminUsers", component: AdminUsers },

  { path: "/user", name: "UserHome", component: UserHome },
  { path: "/user/history", name: "UserHistory", component: UserHistory }, // 👈 new
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
