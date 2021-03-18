<template>
  <div id='controls'>
    
    <label>Playback Mode</label>
    <div class='subControl' v-for="mode in playbackModes" :key='mode.id'>
      <input type='radio' id='mode.id' name='playbackMode' :checked='mode.state'
          :value='mode.id' @change='updatePlaybackMode' v-model='playbackMode'>
      <label for='mode.id'>{{mode.id}}</label>
    </div>

    <label>Audition Mode</label>
    <div class='subControl' v-for="mode in sonificationModes" :key='mode.id'>
      <input type='radio' id='mode.id' name='auditionMode' :value='mode.id' 
          :checked='mode.state' v-model='audition' @change='sendAudition'>
      <label for='mode.id'>{{mode.id}}</label>
    </div>

    <label>Display</label>
    <div class='subControl' v-for="display in displays" :key='display.id'>
      <input type='radio' id='display.id' name='displayMod' :value='display.id' 
          :checked='display.state' v-model='dis' @change='updateDisplay'>      
      <label>{{display.id}}</label>
    </div>

    <label>Dimensions</label>
    <div class='dims'>
      <div v-for='(dim, i) in dims' :key='i'>
        <label>{{dim.axis}}</label>
        <select v-model='dim.value' @change='sendControlPacket'>
          <option v-for='prime in primes' :value='prime' :key='prime'>
            {{prime}}
          </option>
        </select>
      </div>
    </div>

    <label>Octave Shift</label>
    <div class='dims'>
      <div v-for='(dim, i) in dims' :key='i'>
        <label>{{dim.axis}}</label>
        <select v-model='dim.oct' @change='sendControlPacket'>
          <option v-for='oct in octave' :value='oct' :key='oct'>
            {{oct}}
          </option>
        </select>
      </div>
    </div>

    <label>Rotations</label>
    <div class='rotations'>
      <div v-for='(rot, i) in rotations' :key='i'>
        <input type='radio' :value='i' :checked='rot' v-model='checkedRotation' 
            @change='sendControlPacket'
            >
      </div>
    </div>

    <label>Fundamental</label>
    <div class='fundamental'>
      <input type='range' min='0' :max='fundOctaves' step='0.001' 
          v-model='fundSliderVal' @input='updateFund'>
      <label>{{(fundMin * (2 ** fundSliderVal)).toFixed(0)}}</label>
    </div>

    <label>Gain</label>
    <div class='gain'>
      <input type='range' min='0' :max='1' step='0.001' v-model='gainSliderVal' 
          @input='updateMasterGain'>
      <label>{{parseFloat(gainSliderVal).toFixed(2)}}</label>
    </div>
    
    <label>Synth</label>
    <div class='synthControls' v-for='(osc, i) in synths' :key='i'>
      <div class='synthSubControl'>
        <label>{{osc.name}}</label> 
        <input type='range' min='0' max='1' step='0.001' v-model='osc.sliderVal'
            @input='updateSynth(osc.name)'>
      </div>
    </div>
    <label>Filter</label>
    <div class='filter'>
      <input type='range' min='0' max='1' step='0.001' v-model='filterSliderVal'
          @input='updateFilter'>
    </div>


    <div class='buttonBox'>
      <button v-if="multipleRoots" @click='swapRoot'>Swap Root</button>
    </div>
  </div>

</template>

<script>
import EventBus from '../eventBus.js';

export default {
  name: 'Controls', 
  data() {
    return {
      fund: 100,
      playbackMode: 'fixed', 
      audition: 'mono', 
      dis: 'none',
      maxGain: 1,
      fundMin: 50,
      fundOctaves: 6, 
      fundSliderVal: 1,
      multipleRoots: false, 
      gainSliderVal: 0.5, 
      primes: [2, 3, 5, 7, 11, 13, 17, 19],
      octave: [0, -1, -2, -3, -4, -5],
      checkedRotation: 0,
      rotations: Array(6),
      dims: {
        dim1: {
          value: '3',
          name: 'dim1',
          axis: 'X',
          oct: -1
        },
        dim2: {
          value: '11',
          name: 'dim2',
          axis: 'Y',
          oct: -2,
        },
        dim3: {
          value: '7',
          name: 'dim3',
          axis: 'Z',
          oct: -2,
        },
      },
      playbackModes: {
        fixed: {
          id: 'fixed',
          state: false,
        },
        drone: {
          id: 'drone',
          state: true,
        },
        melody: {
          id: 'melody', 
          state: false,
        }
      },

      sonificationModes: {
        mono: {
          id: 'mono',
          state: true,
        },
        binaural: {
          id: 'binaural',
          state: false,
        }
      },

      displays: {
        none: {
          id: 'none',
          state: true,
        },
        rotationShell: {
          id: 'rotationShell',
          state: false,
        },
        fullComplement: {
          id: 'fullComplement',
          state: false,
        }
      },
      
      filterSliderVal: 0.5,
      
      synths: {
        sine: {
          name: 'Sine',
          sliderVal: 0.1,
        },
        tri: {
          name: 'Tri',
          sliderVal: 0.9,
        },
        square: {
          name: 'Square', 
          sliderVal: 0.0,
        },
        saw: {
          name: 'Saw',
          sliderVal: 0.0,
        }
      }
    }
  },
  
  mounted() {
    this.updateFilter()
    
    
  },
  
  methods: {
    
    updateMasterGain() {
      EventBus.$emit('masterGain', this.gainSliderVal)
    },
    
    updateFund() {
      // Adjusts frequencies of all oscillators in proportion to the (newly 
      // adjusted?) fundamental frequency. 
      this.fund = this.fundMin * 2 ** this.fundSliderVal;
      EventBus.$emit('fundamental', this.fund);
    },
    
    updatePlaybackMode() {
      EventBus.$emit('playbackMode', this.playbackMode)
    },
    
    sendAudition() {
      EventBus.$emit('audition', this.audition)
    },
    
    updateDisplay() {
      EventBus.$emit('displays', this.dis)
    },
    
    sendControlPacket() {
      const d = this.dims;
      const dims = [d.dim1.value, d.dim2.value, d.dim3.value].map(d => parseInt(d));
      const octs = [d.dim1.oct, d.dim2.oct, d.dim3.oct].map(d => parseInt(d));
      const controlPacket = {
        playbackMode: this.playbackMode,
        auditionMode: this.audition,
        dims: dims,
        octs: octs,
        rotation: this.checkedRotation,
        fundamental: this.fund,
        masterGain: this.gainSliderVal,
        audition: this.audition
      };
      EventBus.$emit('controlPacket', controlPacket);
    },
    
    updateSynth(oscName) {
      const s = this.synths;
      const oscs = [s.sine, s.tri, s.saw, s.square];
      const total = oscs.map(osc => osc.sliderVal).reduce((a, b) => {
        return parseFloat(a) + parseFloat(b)
      }, 0);
      const surplus = total - 1;
      
      const otherOscs = oscs.filter(osc => {
        console.log(surplus)
        return osc.name != oscName && ((surplus > 0 && osc.sliderVal != 0) || (surplus < 0 && osc.sliderVal != 1))
      });
      otherOscs.forEach(osc => {
        osc.sliderVal = osc.sliderVal - surplus / otherOscs.length;
        if (osc.sliderVal < 0 ) osc.sliderVal = 0;
        if (osc.sliderVal > 1) osc.sliderVal = 1;
      });
      this.sendSynthPacket();
      
    },
    
    updateFilter() {
      this.filter = 20 * (2 ** (10 * this.filterSliderVal));
      this.sendSynthPacket();
    },
    
    sendSynthPacket() {
      const synthPacket = {
        sine: this.synths.sine.sliderVal,
        tri: this.synths.tri.sliderVal,
        saw: this.synths.saw.sliderVal,
        square: this.synths.square.sliderVal,
        filter: this.filter,
      };
      EventBus.$emit('synthPacket', synthPacket);
    },
  }
}
</script>

<style>

#controls {
  z-index: 1;
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 100vh;
  float: right;
  background-color: black;

  display: flex;
  flex-direction: column;
  align-content: flex-start;
  /* justify-content: center; */

  /* border: 1px solid blue; */
}

label {
  color: white;
}

body {
  margin: 0;
}

#controls>label {
  font-size: 20px;
  margin-bottom: 5px;
  margin-top: 20px;
}

.subControl {
  text-align: left;
}

.subControl>label {
  padding-left: 5px;
}

.dims {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}

.dims>div {
  display: flex;
  flex-direction: column;
}

select {
  width: 45px;
}

.rotations {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}

.rotations>div {
  width: 20px;
}

.fundamental {
  background-color: black;
}

.fundamental>input {
  background-color: black;
}

.fundamental>input::-moz-range-track {
  background-color: SteelBlue;
}

.gain {
  background-color: black;
}

.gain>input {
  background-color: black;
}

.gain>input::-moz-range-track {
  background-color: SteelBlue;
}

input:focus {
  outline: none;
}

.buttonBox {
  display: flex;
  justify-content: center;
}

.buttonBox>button {
  width: 100px;
  height: 25px;
}

.filter>input::-moz-range-track {
  background-color: Steelblue;
}

.filter>input {
  background-color: black;
}

.synthSubControl>input::-moz-range-track {
  background-color: SteelbLue;
}

.synthSubControl>input {
  background-color:  black;
  width: 105px;
}

.synthSubControl>label {
  display: inline-block;
  width: 40px;
}

.synthSubControl {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
}

</style>
    
