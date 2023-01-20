<template>
    <div class="d-flex">
        <menu-btn-layout :to="{ name: 'home' }" :active="router.currentRoute.value.name === 'home'">
            {{ $t("menu.home") }}
        </menu-btn-layout>
        <!-- <v-btn class="my-auto" :to="{name: 'home'}" :active="router.currentRoute.value.name === 'home'" variant="text">
            {{$t("menu.home")}}
        </v-btn> -->
        <menu-btn-layout :to="{ name: 'about' }" :active="router.currentRoute.value.name === 'about'">
            {{ $t("menu.about") }}
        </menu-btn-layout>
        <menu-btn-layout :to="{ name: 'contact' }" :active="router.currentRoute.value.name === 'contact'">
            {{ $t("menu.contact") }}
        </menu-btn-layout>
    </div>
</template>
<script setup lang="ts">
import { useRouter } from "vue-router"
import MenuBtnLayout from "./MenuBtnLayout.vue"

const router = useRouter()
// console.log(router);

</script>