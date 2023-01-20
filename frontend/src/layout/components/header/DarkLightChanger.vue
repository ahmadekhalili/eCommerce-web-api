<template>
  <!-- {{theme}} -->
  <v-btn class="ma-2" color="primary" icon variant="plain" @click="changeTheme">
    <v-icon size="large" icon="mdi-theme-light-dark" />
  </v-btn>
</template>
<script setup lang="ts">
import { useTheme } from 'vuetify'
const theme = useTheme()

function changeTheme() {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}
</script>
