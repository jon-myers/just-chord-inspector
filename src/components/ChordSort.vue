<template>
<div class='column'>
  <div class='panel'>
    <div class='layerSelect' v-for="chord in chords" :key='chord.id'>
      <label>{{chord.id}}</label>
      <input type='radio' :value='chord.id' :checked='chord.state' v-model='checkedChords'>
    </div>
  </div>
  <div class='sortPanel'>
    <div class='sortChoice' v-for="(statName, i) in statNames" :key='i' @click='reSort(statName.index)'>

      <label v-show='showIcon[statName.index]'>{{sortDir[dir]}}</label>
    </div>
  </div>
  
  
  <!-- <div class='statNames' v-for="statName in statNames" :key='statName'>
  </div> -->
<div class='statNameBox'>
  <div class='statNames' v-for="statName in statNames" :key='statName.index'>
  <div class='statColumn'>
  </div>
    <div class='label'>{{statName.abbreviation}}</div>
  </div>
</div>
  <div class='chordList'>
    
    <div class='chordBox' v-for="(chord, index) in sortedChords" :key='index' @click='emitChord(chord, index)' :ref='index'>
      <div class='stats' v-for="statName in statNames" :key='statName.index'>
        <div class='statColumn'>
          <div class='label'>{{chord[statName.name]}}</div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>
<script>
import chords5 from '../json/chords5.json';
import chords4 from '../json/chords4.json';
import chords3 from '../json/chords3.json';
import chords2 from '../json/chords2.json';
import chords1 from '../json/chords1.json';
import chords0 from '../json/chords0.json';
import EventBus from '../eventBus.js';
// import BaseIcon from './_base/BaseIcon.vue';
// import DummyImage from '@/assets/svgs/chords1chord0.svg';



export default {
  name: 'ChordSort',
  components: {
    
  },
  data() {
    return {
      checkedChords: '1',
      sortDir: ["\u25B2", "\u25BC"],
      dir: 0,
      chords: {
        0: {
          id: '0',
          chords: chords0,
          state: true
        },
        1: {
          id: '1',
          chords: chords1,
          state: false
        },
        2: {
          id: '2',
          chords: chords2,
          state: false
        },
        3: {
          id: '3',
          chords: chords3,
          state: false
        },
        4: {
          id: '4',
          chords: chords4,
          state: false
        },
        5: {
          id: '5',
          chords: chords5,
          state: false
        }
      },
      statNames: {
        'gen_index': {
          name: 'gen_index',
          abbreviation: 'index',
          index: 0
        },
        'containments': {
          name: 'containments',
          abbreviation: 'cons',
          index: 1
        },
        'dims': {
          name: 'dims',
          abbreviation: 'dims',
          index: 2
        },
        'numOfBranches': {
          name: 'numOfBranches',
          abbreviation: 'brs',
          index: 3,
        },
        'num_distinct_roots': {
          name: 'num_distinct_roots',
          abbreviation: 'roots',
          index: 4
        },
        'symmetry': {
          name: 'symmetry',
          abbreviation: 'sym',
          index: 5
        },
        'stability': {
          name: 'stability',
          abbreviation: 'stab',
          index: 6
        },
        'partial_stability': {
          name: 'partial_stability',
          abbreviation: 'pStab',
          index: 7
        },
        'paths': {
          name: 'paths',
          abbreviation: 'paths',
          index: 8
        },
        'loops': {
          name: 'loops',
          abbreviation: 'loops',
          index: 9
        }
      },
      showIcon: [true, false, false, false]
      
    }
  },
  
  computed: {
    sortedChords() {
      const chords = this.chords[this.checkedChords].chords;
      const index = this.showIcon.indexOf(true);
      const statName = Object.keys(this.statNames)[index];
      return chords.sort((a, b) => {
        if (this.dir === 0) {
          return a[statName] - b[statName]
        } else {
          return b[statName] - a[statName]
        }
      })
    }
  },
  
  methods: {
    
    emitChord(chord, index) {
      const chordPacket = {
        newChord: chord.points, 
        rotationShell: chord.rotation_shell,
        roots: chord.distinct_roots,
      }
      EventBus.$emit('chordPacket', chordPacket);
      if (this.selected) this.selected.classList.remove('selected');
      this.selected = this.$refs[index][0];
      this.selected.classList.add('selected');
      // console.log(this.$el.children[2].querySelector('#'+index.toString()))
      
    },
    
    reSort(index) {
      if (this.showIcon[index] === true) {
        this.dir = Math.abs(this.dir - 1)
      } else {
        this.showIcon = Array(4).fill(false);
        this.showIcon[index] = true;
      }
      
      
      
    }
  }
}
</script>
<style scoped>
body {
  margin: 0
}
.column {
  display: flex;
  position: absolute;
  top: 0px;
  flex-direction: column;
  justify-content: flex-start;
  background-color: black;
  height: 100vh;
  width: 450px;
}

.panel {
  display: flex;
  flex-direction: row;
  justify-content: space-evenly;
  width: 100%;
  height: 50px;
}

.layerSelect {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  /* align-items: center; */
  /* width: 50px; */
}
.layerSelect > input {
  height: 25px;
}

.chordBox {
  display: flex;
  flex: 0 0 auto;
  flex-direction: row;
  justify-content: space-around;
  height: 70px;
  border: 2px solid SteelBlue;  
}

.selectedChordBox {
  display: flex;
  flex: 0 0 auto;
  flex-direction: row;
  justify-content: space-around;
  height: 70px;
  border: 2px solid green; 
}

.sortPanel {
  display: flex;
  flex: 0 0 auto;
  flex-direction: row;
  justify-content: space-around;
  height: 40px;
}

.sortChoice {
  width: 80px;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  height: 100%;
}

.sortChoice > label {
  color: green;
}

.chordList {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  height: 0px;
  justify-content: flex-start;
  overflow-y: auto;
}

.selected {
  border-color: green;
}

.stats {
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  width: 80px;
  height: 100%;
}

/* .statsColumn > div {
  
} */

.label {
  color: white;
}

label {
  color: white;
}

.box {
  width: 70px;
}

.statNameBox {
  display: flex;
  flex-direction: row;
  justify-content: space-evenly;
  height: 50px;
  
}

.statNames {
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  width: 70px;
  /* height: 100%; */
}

</style>
