<template>
    <router-view />
</template>
<script setup lang="ts">
import { useRoute } from "vue-router"
import { i18n } from "@/plugins/i18n";
const route = useRoute()
// console.log(route.params.lang);
i18n.global.locale = route.params.lang.toString()

</script>