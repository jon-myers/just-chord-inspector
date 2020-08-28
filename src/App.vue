<template>
  <div id="app">
    <JustPlot z-index='0'/>
    <ChordSort z-index='1'/>
  </div>
</template>

<script>
// import JustPlot from './components/JustPlot.vue'
import ChordSort from './components/ChordSort.vue';
import JustPlot from './components/JustPlot.vue';


export default {
  name: 'App',
  components: {
    ChordSort,
    JustPlot,
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
  margin: 0;
  background-color: blue;
}


</style>
