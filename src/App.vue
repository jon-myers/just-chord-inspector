<template>
  <div id="app">
    <JustPlot/>
  </div>
</template>

<script>
import JustPlot from './components/JustPlot.vue'

export default {
  name: 'App',
  components: {
    JustPlot
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

body {
  margin: 0
}
</style>
