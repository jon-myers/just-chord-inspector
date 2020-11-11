<template>
<div class="outermost">
  <div class='canvasBox'>
    <canvas ref='canvas' id='canvas'></canvas>
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

const THREE = require('three');

function nestedInclude(arr, value) {
  const stringifiedValue = JSON.stringify(value);
  for (const val of arr) {
    if (JSON.stringify(val) === stringifiedValue) {
      return true
    }
  }
  return false
}

export default {
  name: 'JustPlot',
  data() {
    return {
      sphereColor: 0x6ea5ff,
      rootColor: 0xf0948d,
      primaryRootColor: 0xeb4034,
      shellColor: 0x666378,
      spheres: [],
      roots: [
        [0, 0, 0]
      ],
      currentObj: undefined,
      fund: 100,
      slewTime: 0.05,
      lagTime: 0.01,
      onSpheres: [],
      oldCenter: [0, 0, 0],
      playbackMode: 'fixed',
      audition: 'mono',
      monoGain: 1,
      ambiGain: 0,
      chordOn: true,
      points: [],
      rotationShell: [],

      maxGain: 1,
      fundMin: 50,
      fundOctaves: 6,
      fundSliderVal: 1,
      multipleRoots: false,
      initPosition: [3.5, 6.5, 6.5],
      gainSliderVal: 0.5,
      fullComplement: [],

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

      rotation: 0,
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

      displays: 'none'
    }
  },
  mounted() {
    this.width = window.innerWidth - 650 - 200;
    this.setUpVisuals();
    this.$nextTick(() => this.sendControlPacket());

    window.addEventListener('resize', this.updateWindowSize);

    this.updateDisplay();

    EventBus.$on('chordPacket', chordPacket => {
      this.points = chordPacket.newChord;
      this.roots = chordPacket.roots;
      this.rotationShell = chordPacket.rotationShell;
      this.multipleRoots = this.roots.length > 1;
      this.primaryRoot = chordPacket.primaryRoot;
      this.fullComplement = chordPacket.fullComplement
      console.log(chordPacket)
      this.newChord();
    });
    
    EventBus.$on('currentGains', currentGains => {
      this.currentGains = currentGains;
    });
    
    EventBus.$on('playbackMode', playbackMode => {
      this.playbackMode = playbackMode;
      this.updatePlaybackMode();
    });
    
    EventBus.$on('displays', displays => {
      this.displays = displays;
      this.updateDisplay();
    });
    
    EventBus.$on('controlPacket', cp => {
      this.playbackMode = cp.playbackMode;
      this.rotation = cp.rotation;
      this.newChord();
      
    })
    
    
  },

  methods: {
    
    updateMasterGain() {
      EventBus.$emit('masterGain', this.gainSliderVal)
    },
    
    sendAudition() {
      EventBus.$emit('audition', this.audition)
    },
    
    setUpVisuals() {

      // Set up THREE scene and camera, associate renderer with canvas element,
      // add lighting, enable light to shine on all layers, set camera position  
      const aspect = this.width / window.innerHeight;
      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
      this.mouse = new THREE.Vector2();
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.$refs.canvas
      });
      this.renderer.setSize(this.width, window.innerHeight);

      var light = new THREE.HemisphereLight(0xffffbb, 0x080820, 1);
      this.scene.add(light);
      light.layers.enableAll();
      this.camera.position.x = this.initPosition[0];
      this.camera.position.y = this.initPosition[1];
      this.camera.position.z = this.initPosition[2];
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
        rotation: this.rotation,
        fundamental: this.fund,
        masterGain: this.gainSliderVal,
        audition: this.audition
      };
      EventBus.$emit('controlPacket', controlPacket);
    },


    async newChord() {

      // When triggered by clicking on a chord from the sorting menu, or by 
      // applying a new rotation, removes old chord and instantiates new chord
      // (both audio and visuals). 

      // this.sendControlPacket();
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
      this.rotatedFullComplement = this.fullComplement.map(this.rotate); 
      const extraFullComplement = this.rotatedFullComplement.filter(point => {
        return !nestedInclude(points, point)
      });

      // Rotation shell will only be seen when the 'Rotation Shell' display 
      // checkbox is selected. 
      extraRotShell.forEach(point => this.addSphere(...point));
      extraFullComplement.forEach(point => this.addSphere(...point, 5))

      Promise.all(promises).then(() => {
        this.render()
      })
      this.updatePlaybackMode()
      this.chordOn = true;
    },

    setFreq(obj, init = false) {

      // Ascertains and sets frequency of oscillator associated with given 
      // sphere object, based on its position and chord's fundamental frequency. 

      const pos = [obj.position.x, obj.position.y, obj.position.z];
      const primes = Object.keys(this.dims).map(key => Number(this.dims[key].value));
      const octaves = Object.keys(this.dims).map(key => Number(this.dims[key].oct));
      let freq = this.fund * pos.map((p, i) => primes[i] ** p * 2 ** (p * octaves[i])).reduce((a, b) => a * b, 1);
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
      this.onSpheres.push(sphere);
      sphere.layers.set(1);
      this.maxGain = 1 / (this.onSpheres.length + 1);
      let color = this.roots.includes(index) ? this.rootColor : this.sphereColor;
      if (this.primaryRoot === index) color = this.primaryRootColor;
      sphere.material.color.setHex(color);
    },

    updateFund() {
      // Adjusts frequencies of all oscillators in proportion to the (newly 
      // adjusted?) fundamental frequency. 
      this.fund = this.fundMin * 2 ** this.fundSliderVal;
      EventBus.$emit('fundamental', this.fund);
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
      this.sendControlPacket();
      this.spheres.forEach(sphere => {
        if (sphere.osc) this.setFreq(sphere)
      })
    },

    rotate(point) {
      // For a given point in cartesian coordinates, returns the coordinates of 
      // the 'rotated' version of that point. Each 'rotation' represents a swap
      // of axes. In 3D, for example, there are 6 different 'rotations' of a 
      // given point. `this.rotation` provides the index of the current 
      // rotation.
      const maps = [
        [0, 1, 2],
        [1, 0, 2],
        [0, 2, 1],
        [2, 0, 1],
        [1, 2, 0],
        [2, 1, 0]
      ];
      const translatedPoint = point.map((pt, i) => pt - this.points[this.primaryRoot][i]);
      const rotatedTranslatedPoint = maps[this.rotation].map(i => translatedPoint[i]);
      const rotatedPoint = rotatedTranslatedPoint.map((pt, i) => pt + this.points[this.primaryRoot][i]);
      return rotatedPoint
    },

    updateDisplay() {
      // Enables or disables appropriate layers in order to show or hide rotation
      // shell. Rotation shell spheres are in layer 1; rotation shell connections
      // are in layer 3. 
      this.camera.layers.disableAll();
      console.log(this.displays)
      if (this.displays == 'rotationShell') {
        this.camera.layers.enable(0);
        this.camera.layers.enable(1);
        this.camera.layers.enable(2);
        this.camera.layers.enable(3);
        // this.camera.layers.enable(4);
      } else if (this.displays == 'fullComplement') {
        this.camera.layers.enable(1);
        this.camera.layers.enable(3);
        this.camera.layers.enable(5);
      } else if (this.displays == 'none') {
        this.camera.layers.enable(1);
        this.camera.layers.enable(3);
      }
      this.renderer.render(this.scene, this.camera);
    },

    animate() {
      // When in 'drone' playback mode, ties opacity of each sphere object to 
      // gain of that object. 
      this.animator = requestAnimationFrame(this.animate);
      
      EventBus.$emit('requestGains');
      
      this.onSpheres.forEach((sphere, i) => {
        sphere.material.opacity = this.currentGains[i] * this.points.length
      })
      this.renderer.render(this.scene, this.camera);
    },

    stopAnimate() {
      // Stops animation and returns all spheres to full opacity.
      cancelAnimationFrame(this.animator);
      this.animator = undefined;
      this.onSpheres.forEach(sphere => sphere.material.opacity = 1);
      this.renderer.render(this.scene, this.camera);
      this.animator = undefined;
    },

    updatePlaybackMode() {
      // Adjusts current playback mode to align with appropriate radio box: 
      // 'fixed': Oscillators at full gain.
      // 'off': Oscillators at zero gain.
      // 'drone': Oscillators perform a random walk, starting at full gain.
      // EventBus.$emit('playbackMode', this.playbackMode);    
      if (this.playbackMode === 'drone') {
        if (!this.animator) this.animate();
      } else {
        if (this.animator) this.stopAnimate();
      }
    },

    randomWalk(sphere, attribute, initVal, minVal, maxVal, maxStep) {
      // Iteratively adjusts the value of an attribute of a given sphere object, 
      // starting at initVal, randomly progressing +/- less than the maxStep, 
      // never ranging below the minVal or above the maxVal.
      if (!sphere[attribute]) sphere[attribute] = initVal;
      sphere[attribute] += maxStep * (Math.random() * 2 - 1);
      if (sphere[attribute] > maxVal) attribute === 'azimuth' ? sphere[attribute] -= 2 * Math.PI : sphere[attribute] = maxVal;
      if (sphere[attribute] < minVal) attribute === 'azimuth' ? sphere[attribute] += 2 * Math.PI : sphere[attribute] = minVal;
    },

    updateWindowSize() {

      // THIS NEEDS TO BE FIXED AT SOME POINT; LOOSE NUMBERS NOT TIED TO ANY VARIABLES

      // Adjusts size and aspec ratio of canvas element / renderer according to 
      // current window size, and size of panel components. 

      this.width = window.innerWidth - 650 - 200;
      this.camera.aspect = this.width / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.width, window.innerHeight);
      this.render();
    },

    drawPoints(points) {

      // Given the cartesian coordinates of a point, if not in `this.spheres`, 
      // add new sphere and add cylindrical connections between all spheres. 

      points.forEach(point => {
        if (!nestedInclude(this.spheres.map(sphere => this.getPosition(sphere)), point)) {
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

      const c = this.points ? (this.points.length) / 2 : 0;
      const center = [c, c, c];
      this.camera.position.x = this.initPosition[0];
      this.camera.position.y = this.initPosition[1];
      this.camera.position.z = this.initPosition[2];
      this.camera.lookAt(...center);
      const removes = this.scene.children.filter(child => child.geometry && child.geometry.type === 'CylinderGeometry');
      removes.forEach(child => this.scene.remove(child));
      this.drawConnections(this.rotationShell, 2);
      this.drawConnections(this.rotatedFullComplement, 5)
      this.drawConnections(this.onSpheres.map(sphere => this.getPosition(sphere)), 3);
      this.$nextTick(() => {
        this.renderer.render(this.scene, this.camera)
      })
    },

    getPosition(obj) {

      // Returns cartesian coordinates of sphere object. 

      return [obj.position.x, obj.position.y, obj.position.z]
    },

    addSphere(x, y, z, layer = undefined) {

      // Adds sphere to scene at given cartesian coordinates. 

      const geometry = new THREE.SphereGeometry(0.15, 8, 8);
      const material = new THREE.MeshPhongMaterial({
        color: this.shellColor,
        transparent: true
      });
      const sphere = new THREE.Mesh(geometry, material);
      sphere.position.x = x;
      sphere.position.y = y;
      sphere.position.z = z;
      layer ? sphere.layers.set(layer) : sphere.layers.set(0);
      this.scene.add(sphere);
      this.spheres.push(sphere);
      return sphere
    },

    addConnection(a, b, layer = undefined) {

      // Adds cyllinder to scene between set of point coordinates.

      var geometry = new THREE.CylinderGeometry(0.02, 0.02, 1, 4);
      var material = new THREE.MeshPhongMaterial({
        color: layer === 2 || layer === 5  ? this.shellColor : this.sphereColor
      });
      const cylinder = new THREE.Mesh(geometry, material);
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
  height: 100vh;
}

.outermost {
  position: absolute;
  right: 0;
  height: 100vh;
}

/* #controls {
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
} */
</style>
