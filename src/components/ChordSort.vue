<template>
<div class='column'>
  <div class='topPanel'>
    <div :class="class_.class" :id='class_.id' v-for="(class_, i) in classes" 
    :key='i' @click='selectClass'>
      <label>{{class_.id}}</label>
    </div>
  </div>

  <div class='toggle' v-if='chordView'>
    <div class='panel'>
      <div class='layerSelect' v-for="chord in chords" :key='chord.id'>
        <label>{{chord.id}}</label>
        <input type='radio' :value='chord.id' :checked='chord.state' 
        v-model='checkedChords'>
      </div>
    </div>
    <div class='sortPanel'>
      <div class='sortChoice' v-for="(statName, i) in statNames" :key='i' 
      @click='reSort(statName.index)'>

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

      <div class='chordBox' v-for="(chord, index) in sortedChords" :key='index' 
      @click='emitChord(chord, index)' :ref='index'>
        <div class='stats' v-for="statName in statNames" :key='statName.index'>
          <div class='statColumn'>
            <div class='label'>{{chord[statName.name]}}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <div v-if='!chordView'>
    <div class='shellSizeSelection'>
      <div :class="size === selectedShellSize ? 'selectedShellSizeBox' : 'shellSizeBox'" 
      :id='size' v-for='(size, i) in shellSizes' :key='i' @click='selectShellSize'>
        <label>{{size}}</label>
      </div>
    </div>
    
    <div class='shellSizeSelection'>
      <div :class="i.toString() === selectedShellIndex ? 'selectedShellIndexBox' : 'shellIndexBox'" 
      :id='i' v-for='(index, i) in shellGroup' :key='i' @click='selectShellIndex'>
        <label>{{i}}</label>
      </div>
    </div>
    
    <div class='sortPanel'>
      <div class='sortChoice' v-for="(statName, i) in statNames" :key='i' 
      @click='reSort(statName.index)'>

        <label v-show='showIcon[statName.index]'>{{sortDir[dir]}}</label>
      </div>
    </div>
    
    <div class='statNameBox'>
      <div class='statNames' v-for="statName in statNames" :key='statName.index'>
        <div class='statColumn'>
        </div>
        <div class='label'>{{statName.abbreviation}}</div>
      </div>
    </div>
    <div class='chordList'>

      <div class='chordBox' v-for="(chord, index) in sortedChords" :key='index' 
      @click='emitChord(chord, index)' :ref='index'>
        <div class='stats' v-for="statName in statNames" :key='statName.index'>
          <div class='statColumn'>
            <div class='label'>{{chord[statName.name]}}</div>
          </div>
        </div>
      </div>
    </div>
    
  </div>
</div>
</template>
<script>
// import chords6 from '../json/chords6.json';
import chords5 from '../json/chords5.json';
import chords4 from '../json/chords4.json';
import chords3 from '../json/chords3.json';
import chords2 from '../json/chords2.json';
import chords1 from '../json/chords1.json';
import chords0 from '../json/chords0.json';

import branches0 from '../json/branches0.json';
import branches1 from '../json/branches1.json';
import branches2 from '../json/branches2.json';
import branches3 from '../json/branches3.json';
import branches4 from '../json/branches4.json';
import branches5 from '../json/branches5.json';
import branches6 from '../json/branches6.json';
const branches = [branches0, branches1, branches2, branches3, branches4, branches5, branches6];
import shells from '../json/shells.json';
import EventBus from '../eventBus.js';
// import BaseIcon from './_base/BaseIcon.vue';
// import DummyImage from '@/assets/svgs/chords1chord0.svg';



export default {
  name: 'ChordSort',
  components: {

  },
  data() {
    return {
      selectedShellSize: '4',
      selectedShellIndex: '0',
      shellSizes: Object.keys(shells),
      chordView: true,
      collection: 'branches',
      checkedClass: 'Branches',
      checkedChords: '1',
      sortDir: ["\u25B2", "\u25BC"],
      dir: 0,
      classes: {
        'Branches': {
          id: 'Branches',
          abbreviation: 'branches',
          state: true,
          class: 'classBox selected',
        },
        'Chords': {
          id: 'Chords',
          abbreviation: 'chords',
          state: false,
          class: 'classBox',
        },
        'Shells': {
          id: 'Shells',
          abbreviation: 'shells',
          state: false,
          class: 'classBox',
        }
      },
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
      branches: {
        0: {
          id: '0',
          chords: branches0,
          state: true
        },
        1: {
          id: '1',
          chords: branches1,
          state: false
        },
        2: {
          id: '2',
          chords: branches2,
          state: false
        },
        3: {
          id: '3',
          chords: branches3,
          state: false
        },
        4: {
          id: '4',
          chords: branches4,
          state: false
        },
        5: {
          id: '5',
          chords: branches5,
          state: false
        },
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
        },
        'rotation_shell_size': {
          name: 'rotation_shell_size',
          abbreviation: 'shell',
          index: 10
        }
      },
      showIcon: [true, false, false, false]

    }
  },
  mounted() {
    this.getShellGroup()
  },

  computed: {
    sortedChords() {
      let chords;
      console.log(this.collection);
      if (this.collection === 'shells') {
        chords = this.shellGroup[this.selectedShellIndex]
      } else {
        chords = this[this.collection][this.checkedChords].chords;
      }
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
    
    getShellGroup() {
      // return all the shells of the currently selected size
      const shellsObj = shells[this.selectedShellSize];
      const shellGroup = Object.values(shellsObj).map(shell => {
        return shell.branches.map(branch => {
          return branches[branch.layer][branch.index]
        })
      });
      this.shellGroup = shellGroup
    },

    emitChord(chord, index) {
      const roots = chord.distinct_roots;
      const chordPacket = {
        newChord: chord.points,
        rotationShell: chord.rotation_shell,
        roots: roots,
        primaryRoot: roots[Math.floor(Math.random() * roots.length)]
      }
      EventBus.$emit('chordPacket', chordPacket);
      if (this.selected) this.selected.classList.remove('selected');
      this.selected = this.$refs[index][0];
      this.selected.classList.add('selected');

    },

    reSort(index) {
      if (this.showIcon[index] === true) {
        this.dir = Math.abs(this.dir - 1)
      } else {
        this.showIcon = Array(4).fill(false);
        this.showIcon[index] = true;
      }
    },

    selectClass(e) {
      this.chordView = e.currentTarget.id != 'Shells';
      this.classes[e.currentTarget.id].class = 'classBox selected';
      const others = Object.keys(this.classes).filter(key => key != e.currentTarget.id);
      others.forEach(other => this.classes[other].class = 'classBox');
      this.collection = this.classes[e.currentTarget.id].abbreviation;
      // if (e.currentTarget.id === 'Shells') 
    },
    
    selectShellSize(e) {
      this.selectedShellSize = e.currentTarget.id;
      this.getShellGroup();
    },
    
    selectShellIndex(e) {
      this.selectedShellIndex = e.currentTarget.id;
    }
  }
}
</script>

<style lang="scss" scoped>
@import './styles/chordSort.scss';
</style>
