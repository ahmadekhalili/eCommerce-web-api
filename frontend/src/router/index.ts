import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/:lang(en|fa)?",
      component: () => import("@/i18n/i18nRouter.vue"),
      children: [
        {
          path: "",
          name: "home",
          component: () => import("@/views/home/HomeViewPage.vue"),
        },
        {
          path: "about",
          name: "about",
          // route level code-splitting
          // this generates a separate chunk (About.[hash].js) for this route
          // which is lazy-loaded when the route is visited.
          component: () => import("@/views/AboutView.vue"),
        },
        {
          path: "contact",
          name: "contact",
          component: () => import("../views/ContactView.vue"),
        },
      ],
    },
  ],
});

// router.beforeEach((to, from, next) => {
//   import { i18n } from "@/plugins/i18n";
//   if (to.name !== 'Login' && !isAuthenticated) next({ name: 'Login' })
//   else next()
// })

export default router;
