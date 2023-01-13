<template>
  <v-menu open-on-hover>
    <template #activator="{ props }">
      <v-btn class="ma-2" color="primary" v-bind="props" icon variant="text">
        <v-icon size="large" icon="mdi-translate-variant" />
      </v-btn>
    </template>
    <v-card>
      <v-list :lines="false" density="compact" nav>
        <v-list-subheader>Translation</v-list-subheader>
        <v-list-item v-for="item in items" :key="item.code" :value="item" selected @click="changeLanguage(item.code)"
          :class="`${item.code === $i18n.locale ? 'bg-primary' : ''}`" variant="tonal">
          <v-list-item-title :style="`direction: ${item.rtl ? 'rtl' : 'ltr'};`" v-text="item.name" />
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
</template>
<script setup lang="ts">
import { ref, reactive } from "vue";
import { locales } from "@/i18n/index";
import { i18n } from "@/plugins/i18n";
import { useRouter } from "vue-router"
const items = reactive(locales);

const router = useRouter()


const changeLanguage = function (item: any) {
  i18n.global.locale = item;
  router.push({ params: { lang: item } })
};
</script>
