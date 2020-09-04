<template>
  <div class="outermost">
    <div class='canvasBox'>
      <canvas ref='canvas' id='canvas'></canvas>
    </div>
    <div id='controls'>
      <label>Playback Mode</label>
      <div class='subControl' v-for="mode in playbackModes" :key='mode.id'>
        <input 
          type='radio' 
          id='mode.id' 
          name='playbackMode' 
          :value='mode.id' 
          :checked='mode.state'
          v-model='checked'
          @change='updatePlaybackMode'
        >
        <label for='mode.id'>{{mode.id}}</label>
      </div>
      
      <label>Audition Mode</label>
      <div class='subControl' v-for="mode in sonificationModes" :key='mode.id'>
        <input 
          type='radio' 
          id='mode.id' 
          name='auditionMode' 
          :value='mode.id' 
          :checked='mode.state'
          v-model='audition'
          @change='updateAuditionMode'
        >
        <label for='mode.id'>{{mode.id}}</label>
      </div>
      
      <label>Display</label>
      <div class='subControl' v-for="display in displays" :key='display.id'>
        <input type='checkbox' v-model='display.checked' @change='updateDisplay'>
        <label>{{display.id}}</label>
      </div>
      
      <label>Dimensions</label>
      <div class='dims'>
        <div v-for='(dim, i) in dims' :key='i'>
          <label>{{dim.axis}}</label>
          <select v-model='dim.value' @change='updateDim'>
            <option v-for='prime in primes' :value='prime' :key='prime'>{{prime}}</option>
          </select>
        </div>
      </div>
      
      <label>Octave Shift</label>
      <div class='dims'>
        <div v-for='(dim, i) in dims' :key='i'>
          <label>{{dim.axis}}</label>
          <select v-model='dim.oct' @change='updateDim'>
            <option v-for='oct in octave' :value='oct' :key='oct'>{{oct}}</option>
          </select>
        </div>
      </div>
      
      <label>Rotations</label>
      <div class='rotations'>
        <div v-for='(rot, i) in rotations' :key='i'>
          <input 
            type='radio' 
            :value='i' 
            :checked='rot' 
            v-model='checkedRotation' 
            @change='newChord(points)'
          >
        </div>
      </div>  
      
      <label>Fundamental</label>
      <div class='fundamental'>
        <input 
          type='range' 
          min='0' 
          :max='fundOctaves' 
          step='0.001' 
          v-model='fundSliderVal' 
          @input='updateFund'
        >   
        <label>{{(fundMin * (2 ** fundSliderVal)).toFixed(0)}}</label>
        
      </div>
      <div class='buttonBox'>
        <button v-if="multipleRoots" @click='swapRoot'>Swap Root</button> 
        <button @click='resetAudio'>Reset</button>
      </div> 
    </div>
  </div>
</template>

<script>
// import Vue from 'vue';
import chords5 from '../json/chords5.json';
import chords4 from '../json/chords4.json';
import chords3 from '../json/chords3.json';
import chords2 from '../json/chords2.json';
import chords1 from '../json/chords1.json';
import chords0 from '../json/chords0.json';
import EventBus from '../eventBus.js';
import monoEncodeUrl from 'worklet-loader!./../audioWorklets/monoEncode.js';
import Omnitone from '../../node_modules/omnitone/build/omnitone.min.esm.js';
// import sineProcessor from 'worklet-loader!./../audioWorklets/sineProcessor.js';

const THREE = require('three');
// const lodash = require('lodash');

function nestedInclude(arr, value) {
  const stringifiedValue = JSON.stringify(value);
  for (const val of arr) {
    if (JSON.stringify(val) === stringifiedValue) {
      return true;
    }
  }
  return false;
}

const AudioContext = window.AudioContext || window.webkitAudioContext;

// const inclusiveRange = (start, end) => {
//   return [...Array((end+1) - start).keys()].map(i => i + start)
// }
export default {
  name: 'JustPlot',
  data() {
    return {
      sphereColor: 0x6ea5ff,
      rootColor: 0xf0948d,
      primaryRootColor: 0xeb4034,
      shellColor: 0x666378,
      spheres: [],
      roots: [[0, 0, 0]],
      currentObj: undefined,
      fund: 100,
      slewTime: 0.05,
      lagTime: 0.01,
      onSpheres: [],
      oldCenter: [0, 0, 0],
      checked: 'fixed',
      audition: 'mono', 
      monoGain: 1,
      ambiGain: 0,
      chordOn: true,
      
      maxGain: 1,
      fundMin: 50,
      fundOctaves: 6,
      fundSliderVal: 1,
      multipleRoots: false,
      initPosition: [3.5, 6.5 , 6.5],
      
      chords: {
        0: chords0,
        1: chords1,
        2: chords2,
        3: chords3,
        4: chords4,
        5: chords5
      },
      
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
        off: {
          id: 'off',
          state: false,
        },
        drone: {
          id: 'drone',
          state: true,
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
        rotationShell: {
          id: 'rotationShell',
          checked: false,
        }
      }
    }
  },
  mounted() {
    this.width = window.innerWidth - 450 - 200;
    this.setUpAudio();
    this.setUpVisuals();

    window.addEventListener('resize', this.updateWindowSize);

    this.updateDisplay(); 
    
    EventBus.$on('chordPacket', chordPacket => {
      this.points = chordPacket.newChord;
      this.roots = chordPacket.roots;
      this.rotationShell = chordPacket.rotationShell;
      this.multipleRoots = this.roots.length > 1
      this.primaryRoot = this.roots[Math.floor(Math.random() * this.roots.length)];
      this.newChord();
    })
  },

  methods: {
    
    setUpVisuals() {
      
      // Set up THREE scene and camera, associate renderer with canvas element,
      // add lighting, enable light to shine on all layers, set camera position  
      
      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera( 75, this.width / window.innerHeight, 0.1, 1000 );
      this.mouse = new THREE.Vector2();
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.$refs.canvas
      });
      this.renderer.setSize(this.width, window.innerHeight);
      
      var light = new THREE.HemisphereLight( 0xffffbb, 0x080820, 1 );
      this.scene.add( light );
      light.layers.enableAll();
      this.camera.position.x = this.initPosition[0];
      this.camera.position.y = this.initPosition[1];
      this.camera.position.z = this.initPosition[2];
    },
    
    // probably doesn't really need to be async
    async setUpAudio() {
      
      // Initializes audio nodes, sets initial parameters, and makes connections.
      
      this.ac = new AudioContext();
      await this.ac.audioWorklet.addModule(monoEncodeUrl);
      this.masterGain = this.ac.createGain();
      this.mgDirectOut = this.ac.createGain();
      this.ambiDirectOut = this.ac.createGain();
      this.foaRenderer = Omnitone.createFOARenderer(this.ac);
      await this.foaRenderer.initialize()
      
      this.masterGain.gain.setValueAtTime(0.75, this.ac.currentTime);
      this.mgDirectOut.gain.setValueAtTime(this.monoGain, this.ac.currentTime);
      this.ambiDirectOut.gain.setValueAtTime(this.ambiGain, this.ac.currentTime);
      
      this.masterGain.connect(this.mgDirectOut);
      this.foaRenderer.output.connect(this.ambiDirectOut);
      this.mgDirectOut.connect(this.ac.destination);
      this.ambiDirectOut.connect(this.ac.destination);
    },
    
    resetAudio() {
      
      // Turns off audio context and re initializes. Good to do this as nodes 
      // seem to hang around in memory, eventually causing performance issues. 
      
      this.spheres.forEach(sphere => {
        if (sphere.stopGainNode) this.stopNote(sphere);
        this.scene.remove(sphere)
      });
      this.onSpheres = [];
      this.spheres = [];
      this.cylinders = [];
      this.chordOn = false;
      
      this.ac.close().then(() => {
        this.setUpAudio();
      });
      
    },
    
    async newChord() {

      // When triggered by clicking on a chord from the sorting menu, or by 
      // applying a new rotation, removes old chord and instantiates new chord
      // (both audio and visuals). 
      // const now = this.ac.currentTime;
      // for (;;) {
      //   if (this.ac.currentTime >= now + this.slewTime + this.slewTime) {
      //     this.ac.close();
      //     break
      //   }
      // }
      // await this.setUpAudio();
      if (this.chordOn) {
        this.spheres.forEach(sphere => {
          if (sphere.stopGainNode) this.stopNote(sphere);
          this.scene.remove(sphere)
        });
        this.onSpheres = [];
        this.spheres = [];
        this.cylinders = [];
      }
      const points = this.points.map(this.rotate);
      const promises = points.map(this.turnNewSphereOn);
      const extraRotShell = this.rotationShell.filter(point => {
        return !nestedInclude(points, point)
      });
      
      // Rotation shell will only be seen when the 'Rotation Shell' display 
      // checkbox is selected. 
      extraRotShell.forEach(point => this.addSphere(...point));
      
      Promise.all(promises).then(() => {
        this.render()
      })
      this.updatePlaybackMode()
      this.chordOn = true;
    },
    
    startNote(obj) {
      
      // Sets up the oscillator associated with a given sphere object, creates
      // gains and encodings, makes connections between nodes, and sets initial 
      // parameters. 
      
      // instantiate audio nodes
      obj.osc = this.ac.createOscillator();
      obj.gainNode = this.ac.createGain();
      obj.stopGainNode = this.ac.createGain();
      obj.monoEncode = new AudioWorkletNode(this.ac, 'monoEncode', {numberOfOutputs: 1, outputChannelCount: [4]});
      obj.monoEncode.azimuth = obj.monoEncode.parameters.get('azimuth');
      obj.monoEncode.elevation = obj.monoEncode.parameters.get('elevation');
            
      // connect audio nodes
      obj.osc.connect(obj.gainNode);
      obj.gainNode.connect(obj.stopGainNode);
      obj.stopGainNode.connect(obj.monoEncode);
      obj.monoEncode.connect(this.foaRenderer.input);
      obj.stopGainNode.connect(this.masterGain);
      
      // set parameters
      obj.osc.type = 'triangle';
      this.setFreq(obj, true);
      obj.gainNode.gain.setValueAtTime(0, this.ac.currentTime);
      const gainVal = this.checked == 'drone' ? Math.random() : 1; 
      obj.gainNode.gain.linearRampToValueAtTime(gainVal * this.maxGain, this.ac.currentTime + this.slewTime);
      obj.stopGainNode.gain.setValueAtTime(0, this.ac.currentTime);
      obj.stopGainNode.gain.linearRampToValueAtTime(1, this.ac.currentTime + this.slewTime);
      // randomize ambisonic position
      const azimuth = (Math.random() * 2 - 1) * Math.PI;
      const elevation = (Math.random() - 0.5) * Math.PI;
      obj.monoEncode.azimuth.setValueAtTime(azimuth, this.ac.currentTime); 
      obj.monoEncode.elevation.setValueAtTime(elevation, this.ac.currentTime);
      
      // start oscillator
      obj.osc.start(this.ac.currentTime);
    },
    
    stopNote(obj) {
      
      // Sets gain of oscillator associated with sphere object to zero, stops 
      // the oscillator. I think this should be enough to let all the associated
      // nodes get garbage collected, but not entirely sure. 
      
      obj.stopGainNode.gain.setValueAtTime(1, this.ac.currentTime);
      obj.stopGainNode.gain.linearRampToValueAtTime(0, this.ac.currentTime + this.slewTime);

      obj.osc.stop(this.ac.currentTime + this.slewTime);
      obj.osc.disconnect(obj.gainNode);
      obj.gainNode.disconnect(obj.stopGainNode);
      obj.stopGainNode.disconnect(obj.monoEncode);
      obj.monoEncode.disconnect(this.foaRenderer.input);
      obj.stopGainNode.disconnect(this.masterGain);
      
      
      obj.osc = undefined;
      obj.gainNode = undefined;
      obj.stopGainNode = undefined;
      obj.monoEncode = undefined;
      obj.stopGainNode = undefined;
    },
    
    setFreq(obj, init=false) {
      
      // Ascertains and sets frequency of oscillator associated with given 
      // sphere object, based on its position and chord's fundamental frequency. 
      
      const pos = [obj.position.x, obj.position.y, obj.position.z];
      const primes = Object.keys(this.dims).map(key => Number(this.dims[key].value));
      const octaves = Object.keys(this.dims).map(key => Number(this.dims[key].oct));
      let freq = this.fund * pos.map((p, i) => primes[i]**p * 2**(p * octaves[i])).reduce((a, b) => a * b, 1);
      if (init) {
        obj.osc.frequency.setValueAtTime(freq, this.ac.currentTime)
      } else {
        obj.osc.frequency.setValueAtTime(obj.osc.frequency.value, this.ac.currentTime);
        obj.osc.frequency.exponentialRampToValueAtTime(freq, this.ac.currentTime + this.slewTime)
      }
    },
    
    turnNewSphereOn(point, index) {
      
      // Given cartesian coordinates, adds sphere to scene and starts audio 
      // playback of associated oscillator. 
      
      const sphere = this.addSphere(...point);
      this.startNote(sphere);
      this.onSpheres.push(sphere);
      sphere.layers.set(1);
      this.maxGain = 1 / (this.onSpheres.length + 1);
      let color = this.roots.includes(index) ? this.rootColor: this.sphereColor;
      if (this.primaryRoot === index) color = this.primaryRootColor;
      sphere.material.color.setHex(color);
    },
    
    updateAuditionMode() {
      
      // Allows for toggling between 'mono' and 'binaural' audition modes. 
      // 'Mono' means all oscillators mix to one signal which routes direct to output.
      // 'Binaural' means each oscillator is randomly assigned a spherical position
      // and the total sound is rendered via ambisonics (OMNITONE plugin) to a 
      // stereo signal, best appreciated via headphones. 
      
      if (this.audition === 'mono') {
        this.monoGain = 1;
        this.ambiGain = 0;
      } else {
        this.monoGain = 0;
        this.ambiGain = 1;
      }
      this.ambiDirectOut.gain.setValueAtTime(this.ambiDirectOut.gain.value, this.ac.currentTime);
      this.mgDirectOut.gain.setValueAtTime(this.mgDirectOut.gain.value, this.ac.currentTime);
      this.ambiDirectOut.gain.linearRampToValueAtTime(this.ambiGain, this.ac.currentTime + this.slewTime);
      this.mgDirectOut.gain.linearRampToValueAtTime(this.monoGain, this.ac.currentTime + this.slewTime);
    },
    
    updateFund() {
      
      // Adjusts frequencies of all oscillators in proportion to the (newly 
      // adjusted?) fundamental frequency. 
      
      this.fund = this.fundMin * 2 ** this.fundSliderVal;
      this.spheres.map(sphere => {
        this.setFreq(sphere, false)
      })
    },
    
    swapRoot() {
      
      // In chords with multiple roots, assigns a new primary root, which will
      // appear in a different color and will effect how the chord rotates: 
      // rotations occur about the primary root. 
      
      this.primaryRoot = (this.primaryRoot + 1) % this.roots.length;
      this.newChord();
    },
    
    updateDim() {
      
      // Adjusts frequencies of all oscillators to align with any changes to the 
      // prime or octave shift of a dimension. 
      
      this.spheres.forEach(sphere => {
        if (sphere.osc) this.setFreq(sphere)
      })
    },
    
    rotate(point) {
      
      // For a given point in cartesian coordinates, returns the coordinates of 
      // the 'rotated' version of that point. Each 'rotation' represents a swap
      // of axes. In 3D, for example, there are 6 different 'rotations' of a 
      // given point. `this.checkedRotation` provides the index of the current 
      // rotation.
      
      const maps = [[0, 1, 2], [1, 0, 2], [0, 2, 1], [2, 0, 1], [1, 2, 0], [2, 1, 0]];
      const translatedPoint = point.map((pt, i) => pt - this.points[this.primaryRoot][i]);
      const rotatedTranslatedPoint = maps[this.checkedRotation].map(i => translatedPoint[i]);
      const rotatedPoint = rotatedTranslatedPoint.map((pt, i) => pt + this.points[this.primaryRoot][i]);
      return rotatedPoint
    },
    
    updateDisplay() {
      
      // Enables or disables appropriate layers in order to show or hide rotation
      // shell. Rotation shell spheres are in layer 1; rotation shell connections
      // are in layer 3. 
      
      this.camera.layers.disableAll();
      if (this.displays.rotationShell.checked) {
        this.camera.layers.enableAll();
      } else {
        this.camera.layers.enable(1);
        this.camera.layers.enable(3);
      }
      this.renderer.render(this.scene, this.camera);
    },
    
    animate() {
      
      // When in 'drone' playback mode, ties opacity of each sphere object to 
      // gain of that object. 
      
      this.animator = requestAnimationFrame(this.animate);
      this.onSpheres.forEach(sphere => {
        sphere.material.opacity = sphere.gainNode.gain.value / this.maxGain
      })
      this.renderer.render(this.scene, this.camera);
    },
    
    stopAnimate() {
      
      // Stops animation and returns all spheres to full opacity.
      
      cancelAnimationFrame(this.animator);
      this.animator = undefined;
      this.onSpheres.forEach(sphere => sphere.material.opacity = 1);
      this.renderer.render(this.scene, this.camera);
    },
    
    updatePlaybackMode() {
      
      // Adjusts current playback mode to align with appropriate radio box: 
      // 'fixed': Oscillators at full gain.
      // 'off': Oscillators at zero gain.
      // 'drone': Oscillators perform a random walk, starting at full gain.
      
      
      if (this.checked === 'fixed') {
        if (this.interval) {
          clearInterval(this.interval);
          this.interval = undefined;
          this.onSpheres.forEach(sphere => sphere.gainNode.gain.cancelScheduledValues(this.ac.currentTime));
        }
        this.stopAnimate();
        this.onSpheres.forEach(sphere => {
          sphere.gainNode.gain.setValueAtTime(sphere.gainNode.gain.value, this.ac.currentTime);
          sphere.gainNode.gain.linearRampToValueAtTime(this.maxGain, this.ac.currentTime + this.slewTime);
        })
      } else if (this.checked === 'off') {
        if (this.interval) {
          clearInterval(this.interval);
          this.interval = undefined;
          this.onSpheres.forEach(sphere => sphere.gainNode.gain.cancelScheduledValues(this.ac.currentTime));
        }
        this.stopAnimate();
        this.onSpheres.forEach(sphere => {
          sphere.gainNode.gain.setValueAtTime(sphere.gainNode.gain.value, this.ac.currentTime);
          sphere.gainNode.gain.linearRampToValueAtTime(0, this.ac.currentTime + this.slewTime);
        })
      } else if (this.checked === 'drone') {
        if (!this.interval) {
          this.interval = setInterval(() => {
            if (!this.animator) this.animate();
            this.onSpheres.forEach(sphere => {
              this.randomWalk(sphere, 'walkVal', 1, 0, 1, 0.4);
              sphere.gainNode.gain.setTargetAtTime(sphere.walkVal * this.maxGain, this.ac.currentTime, 1);
            })
          }, 1000)
        }  
      }
    },
    
    randomWalk(sphere, attribute, initVal, minVal, maxVal, maxStep) {
      
      // Iteratively adjusts the value of an attribute of a given sphere object, 
      // starting at initVal, randomly progressing +/- less than the maxStep, 
      // never ranging below the minVal or above the maxVal.
      
      if (!sphere[attribute]) sphere[attribute] = initVal;
      sphere[attribute] += maxStep * (Math.random() * 2 - 1);
      if (sphere[attribute] > maxVal) attribute === 'azimuth' ? sphere[attribute] -= 2 * Math.PI : sphere[attribute] = maxVal;
      if (sphere[attribute] < minVal) attribute === 'azimuth' ? sphere[attribute] += 2 * Math.PI :sphere[attribute] = minVal;      
    },
    
    updateWindowSize() {
      
      // THIS NEEDS TO BE FIXED AT SOME POINT; LOOSE NUMBERS NOT TIED TO ANY VARIABLES
      
      // Adjusts size and aspec ratio of canvas element / renderer according to 
      // current window size, and size of panel components. 
      
      this.width = window.innerWidth - 450 - 200;
      console.log('updating window size');
      this.camera.aspect = this.width / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.width, window.innerHeight);
      this.render();
    },
    
    drawPoints(points) {
      
      // Given the cartesian coordinates of a point, if not in `this.spheres`, 
      // add new sphere and add cylindrical connections between all spheres. 
      
      points.forEach(point => {
        if (! nestedInclude(this.spheres.map(sphere => this.getPosition(sphere)), point)) {
          this.addSphere(...point)
        }
      })
      this.drawConnections(points)
    },
    
    drawConnections(points, layer = undefined) {
      
      // Adds a cyllindrical connection between all sets of spheres in scene if 
      // distance between spheres is exactly equal to 1. 
      
      let combinations = points.flatMap(
        (v, i) => points.slice(i + 1).map(w => [v, w])
      );
      combinations = combinations.filter(comb => {
        const dist = [0, 1, 2].map(i => comb[1][i] - comb[0][i]).filter(num => num != 0);
        return dist.length === 1 && Math.abs(dist[0]) === 1
      });
      combinations.forEach(comb => {
        this.addConnection(...comb, layer)
      })
    },
    
    render() {
      
      // Repositions camera, removes connections, calculates and redraws 
      // connections, and renders scene.
      
      const c = this.points ? (this.points.length) / 2: 0;
      const center = [c, c, c];
      this.camera.position.x = this.initPosition[0];
      this.camera.position.y = this.initPosition[1];
      this.camera.position.z = this.initPosition[2];
      this.camera.lookAt(...center);
      const removes = this.scene.children.filter(child => child.geometry && child.geometry.type === 'CylinderGeometry');
      removes.forEach(child => this.scene.remove(child));
      this.drawConnections(this.spheres.map(sphere => this.getPosition(sphere)), 2);
      this.drawConnections(this.onSpheres.map(sphere => this.getPosition(sphere)), 3);
      this.$nextTick(() => {
        this.renderer.render(this.scene, this.camera)
      })
    },
    
    getPosition(obj) {
      
      // Returns cartesian coordinates of sphere object. 
      
      return [obj.position.x, obj.position.y, obj.position.z]
    },

    addSphere(x, y, z) {
      
      // Adds sphere to scene at given cartesian coordinates. 
      
      const geometry = new THREE.SphereGeometry(0.15, 8, 8);
      const material = new THREE.MeshPhongMaterial( {color: this.shellColor, transparent: true} );
      const sphere = new THREE.Mesh(geometry, material);
      sphere.position.x = x;
      sphere.position.y = y;
      sphere.position.z = z;
      sphere.layers.set(0);
      this.scene.add(sphere);
      this.spheres.push(sphere);
      return sphere
    },

    addConnection(a, b, layer=undefined) {
      
      // Adds cyllinder to scene between set of point coordinates.
      
      var geometry = new THREE.CylinderGeometry( 0.02, 0.02, 1, 4);
      var material = new THREE.MeshPhongMaterial( {color: layer === 2 ? this.shellColor: this.sphereColor});
      const cylinder = new THREE.Mesh( geometry, material );
      cylinder.position.x = (a[0] + b[0]) / 2;
      cylinder.position.y = (a[1] + b[1]) / 2;
      cylinder.position.z = (a[2] + b[2]) / 2;
      const axis = [...Array(3).keys()].filter(i => a[i] - b[i] != 0)[0]
      if (axis == 0) {
        cylinder.rotateZ(Math.PI / 2)
      } else if (axis == 2) {
        cylinder.rotateX(Math.PI / 2)
      }
      if (layer) cylinder.layers.set(layer)
      this.scene.add(cylinder);
      this.cylinders.push(cylinder);
    },
  }
}
</script>



<style scoped>


.canvasBox {
  position: relative;
  right: 200px;
}
.outermost {
  position: absolute;
  right: 0;
  /* width: 100%; */
}

#controls {
  z-index: 1;
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 100%;
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

#controls > label {
  font-size: 20px;
  margin-bottom: 5px;
  margin-top: 20px;
}

.subControl {
  text-align: left;
}
 .subControl > label {
   padding-left: 5px;
 }
 
 .dims {
  display: flex;
  flex-direction: row;
  justify-content: space-around;
 }
 
 .dims > div {
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
 
 .rotations > div {
   width: 20px;
 }
 
 .fundamental {
   background-color: black;
 }
 
 .fundamental > input {
   background-color: black;
 }
 
 .fundamental > input::-moz-range-track {
   background-color: SteelBlue;
   /* color: black; */
   /* height: 30px; */
  }
  
  input:focus {
    outline-width: 0
  }
  
  .buttonBox {
    display: flex;
    justify-content: center;
  }
  
  .buttonBox > button {
    width: 100px;
    height: 25px;
  }

</style>
