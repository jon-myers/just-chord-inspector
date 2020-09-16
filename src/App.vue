<template>
  <div id="app">
    <ChordSort z-index='0'/>
    <JustPlot z-index='0'/>
    
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
  height: 100vh;
}

html {
  overflow: hidden;
}




</style>
