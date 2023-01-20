<template>

  <v-app class="bg-surface" style="width: 100vw;">
    <v-locale-provider :rtl="$t('base.direction') === 'RTL'">
      <v-hover v-slot="{ isHovering, props }">
        <header v-bind="props" class="b-glass header-default" :style="`
         background-color: ${(isHovering || !topHideBackgroundHeader) && $vuetify?.theme?.current?.colors?.background ?
    $vuetify?.theme?.current?.colors?.background + 'ff' :
    $vuetify?.theme?.current?.colors?.background + $vuetify?.theme?.current?.variables?.alpha1};
        `">
          <section class="d-flex flex-row" style="height: 74px">
            <!-- logo -->
            <DefaultLayoutLogo />
            <!-- space  -->
            <v-spacer />
            <!-- menu -->
            <HeaderMenu />
            <!-- space  -->
            <v-spacer />


            <!-- space  -->
            <!-- <v-spacer class="d-none d-sm-block" /> -->
            <!-- sign-in | sign-up | user -->
            <DefaultLayoutUserSign />
            <!-- cart -->
            <DefaultLayoutCart />
            <!-- lang changer -->
            <LanguageChanger />
          </section>
          <!-- <section class="d-flex flex-row"> -->

          <!-- spacer -->
          <!-- <v-spacer /> -->
          <!-- search -->
          <!-- <DefaultLayoutSearch /> -->

          <!-- </section> -->
        </header>
      </v-hover>
      <slot />
      <FooterDefault />
    </v-locale-provider>
  </v-app>
</template>
<script setup lang="ts">
export interface Props {
  topHideBackgroundHeader: boolean
}
import LanguageChanger from "./components/header/LanguageChanger.vue";
import HeaderMenu from "./components/menu/HeaderMenu.vue";
import DefaultLayoutLogo from "./components/header/DefaultLayoutLogo.vue";
import DefaultLayoutUserSign from "./components/header/DefaultLayoutUserSign.vue";
import DefaultLayoutCart from "./components/header/defaultLayoutCart.vue";
import FooterDefault from "./components/footer/FooterDefault.vue";

withDefaults(defineProps<Props>(), {
  topHideBackgroundHeader: false
})
</script>

<style scoped>
.header-default {
  transition: background-color 1s;
  -webkit-transition: background-color 1s;
  min-height: 74px;
  position: fixed;
  z-index: 3;
  width: 100%;
}
</style>