<template>
    <router-link :to="to" style="cursor: pointer" class="text-decoration-none">
        <v-hover v-slot="{ isHovering, props }">
            <v-card height="70px" :rounded="0" :elevation="isHovering ? 0 : 0" v-bind="props"
                :class="`pa-2 pt-5 text-subtitle-1 ${active ? 'text-primary' : 'text-text-primary'}`"
                :style="`background-color: #0000;`">
                <slot />
            </v-card>
            <v-divider v-if="isHovering" color="primary" thickness=4 />

        </v-hover>
    </router-link>


</template>
<script setup lang="ts">
export interface Props {
    active: boolean
    to: any
}

withDefaults(defineProps<Props>(), {
    active: false
})
</script>