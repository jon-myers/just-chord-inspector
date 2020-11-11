<template>
  <div id="app">
    <ChordSort z-index='0'/>
    <JustPlot z-index='0'/>
    <Controls />
    <Audio/>
    
    
  </div>
</template>

<script>
import JustPlot from './components/JustPlot.vue'
import ChordSort from './components/ChordSort.vue';
// import JustPlot from './components/JustPlot.vue';
import Audio from './components/Audio.vue';
import Controls from './components/Controls.vue';

export default {
  name: 'App',
  components: {
    ChordSort,
    JustPlot,
    Audio,
    Controls,
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
