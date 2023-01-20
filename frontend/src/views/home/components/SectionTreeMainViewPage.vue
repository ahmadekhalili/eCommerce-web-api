<template>
    <v-card-title class="text-center font-weight-regular pt-16">ادکلن های برگزیده</v-card-title>
    <carousel :settings="settings" :breakpoints="breakpoints" :wrap-around="true">
        <slide v-for="slide in 10" :key="slide">

            <v-card class="ma-2 carousel__item" height="300px" width="250px"
                :style="`text-align: ${$t('base.direction') === 'RTL' ? 'right' : 'left'}`" elevation="2">
                <v-card-title>عنوان</v-card-title>
                <v-img :src="image1" />
            </v-card>
        </slide>

        <template #addons>
            <Navigation />
        </template>
    </carousel>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue"
import { Carousel, Navigation, Slide } from 'vue3-carousel'


let image1 = "https://i.picsum.photos/id/20/500/300.jpg?hmac=bkIR6-136Q_P9IU1bjU0JeFQlSBRG-FLvaynW1V0pFc"


const settings = ref({
    itemsToShow: 1,
    snapAlign: 'center',
})

const breakpoints = ref({
    // 700px and up
    700: {
        itemsToShow: 3.5,
        snapAlign: 'center',
    },
    // 1024 and up
    1024: {
        itemsToShow: 4,
        snapAlign: 'start',
    },
})



</script>
