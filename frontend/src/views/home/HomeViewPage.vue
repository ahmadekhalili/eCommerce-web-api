<template>
  <default :top-hide-background-header="arrivedState?.top">

    <!--  section One -->
    <img alt="تصویر زمینه" style="width:100%;height: calc(100vh - 35px);object-fit:cover" cover :src="background" />
    <v-btn class="mx-auto mt-n7" color="white" icon @click="getSectionTwo">
      <v-icon size="x-large">mdi-chevron-down</v-icon>
    </v-btn>

    <!-- section Two -->
    <div id="main-section-two" class="bg-surface">

      <v-row class="pa-3 pl-6 pr-8">
        <v-col cols="12" sm="6" md="4">
          <SectionTwoCards :image="image1" :title="'عطر با رایحه مرکبات'" :url="'fg'" />
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <SectionTwoCards :image="image2" :title="'عطر با رایحه مرکبات'" :url="'fg'" />
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <SectionTwoCards :image="image3" :title="'عطر با رایحه مرکبات'" :url="'fg'" />
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <SectionTwoCards :image="image4" :title="'عطر با رایحه مرکبات'" :url="'fg'" />
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <SectionTwoCards :image="image5" :title="'عطر با رایحه مرکبات'" :url="'fg'" />
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <SectionTwoCards :image="image6" :title="'عطر با رایحه مرکبات'" :url="'fg'" />
        </v-col>
      </v-row>

    </div>

    <!-- section Tree -->
    <SectionTreeMainViewPage />
  </default>
</template>

<script setup lang="ts">
import { useScroll } from "@vueuse/core";

import image1 from "@/assets/pre-images/main-section2/1.webp"
import image2 from "@/assets/pre-images/main-section2/2.webp"
import image3 from "@/assets/pre-images/main-section2/3.webp"
import image4 from "@/assets/pre-images/main-section2/4.webp"
import image5 from "@/assets/pre-images/main-section2/5.webp"
import image6 from "@/assets/pre-images/main-section2/6.webp"

import background from "@/assets/background1.jpg";

import Default from "@/layout/Default.vue";

import api from "../product/api/api";
import SectionTwoCards from "./components/SectionTwoCards.vue";
import SectionTreeMainViewPage from "./components/SectionTreeMainViewPage.vue";

api.get("/posts/");


// check scroll top for active header glass
const { arrivedState } = useScroll(document, { behavior: 'smooth' });

// get scroll to section two in main page
function getSectionTwo() {
  document.getElementById("main-page")?.scrollTo({
    top: (document.getElementById('main-section-two')?.offsetTop || 0) - 60,
    behavior: 'smooth',
  })
}

</script>
