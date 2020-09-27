<template>
  <div>
  </div>
</template>

<script>

import monoEncodeUrl from 'worklet-loader!./../audioWorklets/monoEncode.js';
import Omnitone from '../../node_modules/omnitone/build/omnitone.min.esm.js';
import EventBus from '../eventBus.js';

const AudioContext = window.AudioContext || window.webkitAudioContext;

export default {
  name: 'Audio',
  data() {
    return {
      oscBankSize: 10,
      slewTime: 0.01,
      masterGain: 0.5,
      chord: [],
      
    }
  },
  
  mounted() {
    this.setUpAudio();
    
    EventBus.$on('chordPacket', chordPacket => {
      this.initializeOscBank();
      this.chord = chordPacket.newChord;
      this.primaryRoot = chordPacket.primaryRoot;
      this.updateChord();
    });
    
    EventBus.$on('controlPacket', controlPacket => {
      // this.initializeOscBank();
      this.dims = controlPacket.dims;
      this.octs = controlPacket.octs;
      this.fund = controlPacket.fundamental;
      this.rotation = controlPacket.rotation;
      this.masterGain = controlPacket.masterGain;
      this.audition = controlPacket.audition;
      this.updateChord();
    });
    
    EventBus.$on('masterGain', gain => {
      this.masterGain = gain;
      this.updateMasterGain();
    });
    
    EventBus.$on('audition', audition => {
      if (this.audition != audition) {
        this.audition = audition;
        const mg = this.monoMix.gain;
        const ag = this.ambiMix.gain;
        if (this.audition === 'mono') {
          mg.setValueAtTime(0, this.now());
          mg.linearRampToValueAtTime(1, this.now() + this.slewTime);
          ag.setValueAtTime(1, this.now());
          ag.linearRampToValueAtTime(0, this.now() + this.slewTime);
        } else if (this.audition === 'binaural') {
          mg.setValueAtTime(1, this.now());
          mg.linearRampToValueAtTime(0, this.now() + this.slewTime);
          ag.setValueAtTime(0, this.now());
          ag.linearRampToValueAtTime(1, this.now() + this.slewTime);
        }    
      }
    });
    
    EventBus.$on('playbackMode', playbackMode => {
      this.playbackMode = playbackMode;
      this.updatePlaybackMode();
    });
    
    EventBus.$on('fundamental', fund => {
      const oldFund = this.fund;
      this.fund = fund;
      const ratio = this.fund / oldFund;
      this.oscBank.forEach(oscObj => {
        const freqParam = oscObj.osc.frequency;
        const current = freqParam.value;
        freqParam.setValueAtTime(current, this.now());
        freqParam.exponentialRampToValueAtTime(current * ratio, this.now());
      })
    });
    
    EventBus.$on('requestGains', () => {
      const objs = this.oscBank.filter((_, i) => i < this.chord.length);
      const gains = objs.map(obj => obj.gainNode.gain.value);
      EventBus.$emit('currentGains', gains);
    })
      
  },
  
  methods: {
    
    now() {
      return this.ac.currentTime
    },
    
    rotate(point) {
      
      // For a given point in cartesian coordinates, returns the coordinates of 
      // the 'rotated' version of that point. Each 'rotation' represents a swap
      // of axes. In 3D, for example, there are 6 different 'rotations' of a 
      // given point. `this.checkedRotation` provides the index of the current 
      // rotation.
      const pr = this.primaryRoot;
      const maps = [
        [0, 1, 2], 
        [1, 0, 2], 
        [0, 2, 1], 
        [2, 0, 1], 
        [1, 2, 0], 
        [2, 1, 0]
      ];
      const translated = point.map((pt, i) => pt - this.chord[pr][i]);
      const rotated = maps[this.rotation].map(i => translated[i]);
      const rotatedPoint = rotated.map((pt, i) => pt + this.chord[pr][i]);
      return rotatedPoint
    },
    
    updateChord() {
      if (this.ac.state === 'suspended') this.ac.resume();
      this.chord.forEach((note, n) => {
        const rotNote = this.rotate(note);
        const mult = this.dims.map((dim, i) => {
          return (dim ** rotNote[i]) * (2 ** (rotNote[i] * this.octs[i]))
        });
        const freq = this.fund * mult.reduce((a, b) => a * b, 1);
        const osc = this.oscBank[n].osc;
        const gainNode = this.oscBank[n].gainNode;
        const encode = this.oscBank[n].ambiEncode;
        osc.frequency.setValueAtTime(freq, this.now() + this.slewTime);
        const level = 1 / this.chord.length;
        gainNode.gain.setValueAtTime(0, this.now()+this.slewTime);
        gainNode.gain.linearRampToValueAtTime(level, this.now() + 2 * this.slewTime);
        const az = Math.PI * (2 * Math.random() - 1);
        const el = Math.PI * (Math.random() - 0.5);
        encode.azimuth.setValueAtTime(az, this.now()+this.slewTime);
        encode.elevation.setValueAtTime(el, this.now()+this.slewTime);
      })
      this.updatePlaybackMode();
    },
    
    updatePlaybackMode() {
      if (this.playbackMode === 'drone') {
        if (!this.interval) {
          this.interval = setInterval(() => {
            this.chord.forEach((_, i) => {
              const gainVal = this.oscBank[i].gainNode.gain.value * this.chord.length;
              this.randomWalk(this.oscBank[i], gainVal, 0, 1, 0.5)
            })
          }, 1000)
        }
      } else if (this.playbackMode === 'fixed') {
        if (this.interval) {
          clearInterval(this.interval);
          this.interval = undefined;
          this.chord.forEach((_, i) => {
            const gain = this.oscBank[i].gainNode.gain;
            gain.setValueAtTime(gain.value, this.now());
            const level = 1 / this.chord.length;
            gain.linearRampToValueAtTime(level, this.now() + this.slewTime);
          })
        }
      }
    },
    
    randomWalk(oscObj, initVal, minVal, maxVal, maxStep) {
      oscObj.walkVal += maxStep * (Math.random() * 2 - 1);
      if (oscObj.walkVal > maxVal) oscObj.walkVal = maxVal;
      if (oscObj.walkVal < minVal) oscObj.walkVal = minVal;
      const gain = oscObj.gainNode.gain;
      const maxLevel = 1 / this.chord.length;
      gain.setTargetAtTime(oscObj.walkVal * maxLevel, this.now(), 1);
  
    },
    
    updateMasterGain() {
      const gain = this.masterGainNode.gain;
      gain.setValueAtTime(gain.value, this.now());
      gain.linearRampToValueAtTime(this.masterGain, this.now() + this.slewTime)
    },
    
    async setUpAudio() {
      this.ac = new AudioContext();
      await this.ac.audioWorklet.addModule(monoEncodeUrl);
      this.monoMix = this.ac.createGain();
      this.ambiMix = this.ac.createGain();
      this.masterGainNode = this.ac.createGain();
      this.foaRenderer = Omnitone.createFOARenderer(this.ac);
      await this.foaRenderer.initialize();
      this.oscBank = [...Array(this.oscBankSize)].map(() => this.makeOsc());
      
      // this.monoMix.gain.setValueAtTime(this.masterGain, this.now())
      this.masterGainNode.gain.setValueAtTime(this.masterGain, this.now());
      
      this.monoMix.connect(this.masterGainNode);
      this.ambiMix.connect(this.foaRenderer.input);
      this.foaRenderer.output.connect(this.masterGainNode);
      this.masterGainNode.connect(this.ac.destination)
    },
    
    makeOsc() {
      const osc = this.ac.createOscillator();
      osc.type = 'triangle';
      const gainNode = this.ac.createGain();
      const options = {numberOfOutputs: 1, outputChannelCount: [4]}
      const ambiEncode = new AudioWorkletNode(this.ac, 'monoEncode', options);
      ambiEncode.azimuth = ambiEncode.parameters.get('azimuth');
      ambiEncode.elevation = ambiEncode.parameters.get('elevation');
      gainNode.gain.setValueAtTime(0, this.ac.currentTime)
      osc.connect(gainNode);
      gainNode.connect(this.monoMix);
      gainNode.connect(ambiEncode);
      ambiEncode.connect(this.foaRenderer.input);
      
      osc.start(this.now());
      const obj = {
        osc: osc,
        gainNode: gainNode,
        ambiEncode: ambiEncode,
        walkVal: 1,
      };
      return obj      
    },
    
    initializeOscBank() {
      this.oscBank.forEach(obj => {
        obj.gainNode.gain.cancelScheduledValues(this.now());
        obj.gainNode.gain.setValueAtTime(obj.gainNode.gain.value, this.now());
        obj.gainNode.gain.linearRampToValueAtTime(0, this.now() + this.slewTime);
      })
    }
  }
}
</script>
