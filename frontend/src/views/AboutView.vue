<template>
  <div>
    <Datepicker v-model="selectedDates" type="range" @change="onDateChange" range :enable-time-picker="false"
      format="MMM dd" />
  </div>
</template>

<script>
import Datepicker from "@vuepic/vue-datepicker"

export default {
  components: {
    Datepicker,
  },
  data() {
    return {
      startDate: new Date(new Date().setDate(new Date().getDate() - 7)),
      endDate: new Date(),
      selectedDates: [this.startDate, this.endDate],
    }
  },
  methods: {
    onDateChange() {
      this.$emit("date-change", this.selectedDates)
    },
  },
}
</script>
