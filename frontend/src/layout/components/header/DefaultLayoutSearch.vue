<template>
    <v-text-field class="ma-2 secondary d-none d-sm-block" prepend-inner-icon="mdi-magnify" density="compact"
        :label="$t('words.search')" hide-details color="primary" />
    <v-btn class="d-block d-sm-none ma-2" color="primary" icon variant="plain">
        <v-icon size="large" icon="mdi-account-circle" />
    </v-btn>
</template>