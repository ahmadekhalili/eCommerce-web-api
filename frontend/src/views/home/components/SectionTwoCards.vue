<template>
    <v-responsive :aspect-ratio="3 / 4" content-class="pa-2">
        <v-hover v-slot="{ isHovering, props }">


            <v-card class="h-100" v-bind="props">
                <v-img class="bg-white" height="100%" :src="image"
                    :style="`transition: all 5s ease-in-out;${isHovering ? 'transform: scale(1.2);' : ''}`" cover>
                    <div
                        style="background-image: linear-gradient(to top,rgba(4,4,4,.65),rgba(54,54,54,.2));height: 100%">

                    </div>
                </v-img>
                <div class="pb-4 text-center" style="position: absolute;bottom: 0;width: 100%;">
                    <v-card-title class="text-h6 text-md-h5 text-lg-h4 font-weight-light text-white mb-10">
                        {{ title }}
                    </v-card-title>
                    <v-btn variant="outlined" class="mb-10 text-white">
                        مشاهده کالاها
                    </v-btn>
                </div>
            </v-card>
        </v-hover>
    </v-responsive>
</template>
<script setup lang="ts">
export interface Props {
    image: string
    title: string
    url: string
}

defineProps<Props>()
</script>