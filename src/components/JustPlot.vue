<template>
  <div class="hello">
    <canvas ref='canvas'></canvas>
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
    </div>
  </div>
</template>

<script>
import chords5 from '../json/chords4.json';
import chords4 from '../json/chords4.json';
import chords3 from '../json/chords3.json';
import chords2 from '../json/chords2.json';
import chords1 from '../json/chords1.json';
import EventBus from '../eventBus.js';
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
      gridColor: 0x6c6e73,
      sphereColor: 0x240f7a,
      hoverColor: 0x54a5eb,
      sphereOnColor: 0x240f7a,
      spheres: [],
      currentObj: undefined,
      fund: 100,
      slewTime: 0.01,
      onSpheres: [],
      oldCenter: [0, 0, 0],
      checked: 'fixed',
      maxGain: 1,
      fundMin: 50,
      fundOctaves: 6,
      fundSliderVal: 1,
      
      chords: {
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
          value: '5',
          name: 'dim2',
          axis: 'Y',
          oct: -1,
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
      
      displays: {
        spheres: {
          id: 'spheres',
          checked: true,
        },
        possibilities: {
          id: 'possibilites',
          checked: true,
        },
        connections: {
          id: 'connections',
          checked: true,
        }
      }
    }
  },
  mounted() {
    this.setUpAudio();
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.$refs.canvas
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    window.addEventListener('resize', this.updateWindowSize);
    
    // this.newChord(chords4, 1)
    
    var light = new THREE.HemisphereLight( 0xffffbb, 0x080820, 1 );
    this.scene.add( light );
    
    // enable all layers
    this.camera.layers.enable(0);
    this.camera.layers.enable(1);
    this.camera.layers.enable(2);
    this.camera.layers.enable(3);
    
    light.layers.enable(0);
    light.layers.enable(1);
    light.layers.enable(2);
    light.layers.enable(3);
    
    this.raycaster.layers.enable(0);
    this.raycaster.layers.enable(1);
    
    this.initPosition = [2.5, 5 , 5];

    this.camera.position.x = this.initPosition[0];
    this.camera.position.y = this.initPosition[1];
    this.camera.position.z = this.initPosition[2];
    
    this.camera.lookAt(0, 0, 0);    
    this.renderer.render(this.scene, this.camera);
    
    EventBus.$on('newChord', chord => {
      this.newChord(chord)
    });
    
  },

  methods: {
    
    updateFund() {
      
      this.fund = this.fundMin * 2 ** this.fundSliderVal;
      this.spheres.map(sphere => {
        this.setFreq(sphere, false)
      })
    },
    
    newChord(points) {
      this.points = points;
      this.spheres.forEach(sphere => {
        this.stopNote(sphere);
        this.scene.remove(sphere)
      });
      this.onSpheres = [];
      this.spheres = [];
      const maps = [[0, 1, 2], [1, 0, 2], [0, 2, 1], [2, 0, 1], [1, 2, 0], [2, 1, 0]];
      points = points.map(point => maps[this.checkedRotation].map(i => point[i]));
      // console.log(points, trialPoints)
      points.forEach(point => this.turnNewSphereOn(point));
      this.render()
    },
    
    updateDim() {
      this.spheres.forEach(sphere => {
        if (sphere.osc) this.setFreq(sphere)
      })
    },
    
    updateDisplay() {
      this.camera.layers.disableAll();
      if (this.displays.spheres.checked) {
        this.camera.layers.enable(1);
        if (this.displays.connections.checked) {
          this.camera.layers.enable(3);
        }
      } 
      
      if (this.displays.possibilities.checked) {
        this.camera.layers.enable(0);
        if (this.displays.connections.checked) this.camera.layers.enable(2);
      }
      this.renderer.render(this.scene, this.camera);
      
    },
    
    animate() {
      this.animator = requestAnimationFrame(this.animate);
      this.onSpheres.forEach(sphere => {
        sphere.material.opacity = sphere.gainNode.gain.value / this.maxGain
      })
      this.renderer.render(this.scene, this.camera);
    },
    
    stopAnimate() {
      cancelAnimationFrame(this.animator);
      this.animator = undefined;
      this.onSpheres.forEach(sphere => sphere.material.opacity = 1);
      this.renderer.render(this.scene, this.camera);
    },
    
    updatePlaybackMode() {
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
              
              if (!sphere.walkVal) sphere.walkVal = 1;
              sphere.walkVal += 0.4 * (Math.random() * 2 - 1);
              if (sphere.walkVal > 1) sphere.walkVal = 1;
              if (sphere.walkVal < 0) sphere.walkVal = 0;
              sphere.gainNode.gain.setTargetAtTime(sphere.walkVal * this.maxGain, this.ac.currentTime, 1);
            })
          }, 1000)
        }  
      }
    },
    
    updateWindowSize() {
      console.log('updating window size');
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.render();
    },
    
    getCenter() {
      let x = this.spheres.map(sphere => sphere.position.x);
      let y = this.spheres.map(sphere => sphere.position.y);
      let z = this.spheres.map(sphere => sphere.position.z);
      x = (Math.max(...x) + Math.min(...x)) / 2;
      y = (Math.max(...y) + Math.min(...y)) / 2;
      z = (Math.max(...z) + Math.min(...z)) / 2;
      
      return [x, y, z]
    },
    
    drawPoints(points) {
      points.forEach(point => {
        if (! nestedInclude(this.spheres.map(sphere => this.getPosition(sphere)), point)) {
          this.addSphere(...point)
        }
      })
      this.getConnections(points)
    },
    
    getConnections(points, layer = undefined) {
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
    
    setUpAudio() {
      this.ac = new AudioContext();
      this.masterGain = this.ac.createGain();
      
      this.masterGain.gain.setValueAtTime(0.1, this.ac.currentTime);
      
      this.masterGain.connect(this.ac.destination);
    },
    
    setFreq(obj, init=false) {
      const pos = [obj.position.x, obj.position.y, obj.position.z];
      const primes = Object.keys(this.dims).map(key => Number(this.dims[key].value));
      const octaves = Object.keys(this.dims).map(key => Number(this.dims[key].oct));
      // const adjustedFund = this.fund / 2 ** octaves.reduce((a, b) => a + b, 0);
      let freq = this.fund * pos.map((p, i) => primes[i]**p * 2**(p * octaves[i])).reduce((a, b) => a * b, 1);
      // while (freq > 400) freq /= 2;
      // while (freq < 200) freq *= 2;
      if (init) {
        obj.osc.frequency.setValueAtTime(freq, this.ac.currentTime)
      } else {
        obj.osc.frequency.setValueAtTime(obj.osc.frequency.value, this.ac.currentTime);
        obj.osc.frequency.exponentialRampToValueAtTime(freq, this.ac.currentTime + this.slewTime)
      }
    },
    
    startNote(obj) {
      // create audio nodes
      obj.osc = this.ac.createOscillator();
      obj.gainNode = this.ac.createGain();
      
      // connect audio nodes
      obj.osc.connect(obj.gainNode);
      obj.gainNode.connect(this.masterGain);
      
      //
      obj.osc.type = 'triangle';
      this.setFreq(obj, true);
      obj.gainNode.gain.setValueAtTime(0, this.ac.currentTime);
      obj.gainNode.gain.linearRampToValueAtTime(Math.random() * this.maxGain, this.ac.currentTime + this.slewTime);
      
      obj.osc.start(this.ac.currentTime);
    },
    
    stopNote(obj) {
      obj.gainNode.gain.setValueAtTime(this.maxGain, this.ac.currentTime);
      obj.gainNode.gain.linearRampToValueAtTime(0, this.ac.currentTime + this.slewTime);
      obj.osc.stop(this.ac.currentTime + this.slewTime);
      obj.osc = undefined;
    },
    
    hoverOverSphere(obj) {
      if (obj != this.currentObj) {
        if (this.currentObj && ! this.onSpheres.includes(this.currentObj)) {
          this.currentObj.material.color.setHex(this.sphereColor);
          if (this.currentObj.osc) this.stopNote(this.currentObj);
        }
        this.currentObj = obj
      }
      if (this.ac.state === 'suspended') this.ac.resume();
      if (!obj.osc) this.startNote(obj);
      if (! this.onSpheres.includes(obj)) {
        obj.material.color.setHex(this.hoverColor);
        this.renderer.render(this.scene, this.camera);
      }
    },
    
    mouseMove(e) {
      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = (1 - e.clientY / window.innerHeight) * 2 - 1;
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const testSet = this.displays.possibilities.checked ? this.spheres: this.onSpheres;
      const intersects = this.raycaster.intersectObjects(testSet);
      if (intersects[0]) {
        this.hoverOverSphere(intersects[0].object);
      } else {
        if (this.currentObj && this.currentObj.material.color.getHex() === this.hoverColor && ! this.onSpheres.includes(this.currentObj)) {
          this.currentObj.material.color.setHex(this.sphereColor);
          this.stopNote(this.currentObj);
          this.renderer.render(this.scene, this.camera);
          this.currentObj = undefined;    
        }
      }
    },
    
    click() {
      if (this.currentObj) {
        if (this.onSpheres.includes(this.currentObj)) {
          this.turnSphereOff();
        } else {
          this.turnSphereOn();
        } 
      }
    },
    
    turnNewSphereOn(point) {
      const sphere = this.addSphere(...point);
      this.startNote(sphere);
      this.onSpheres.push(sphere);
      sphere.layers.set(1);
      this.maxGain = 1 / (this.onSpheres.length + 1);
      this.updatePlaybackMode();
      sphere.material.color.setHex(this.sphereOnColor);
      this.render()
    },
    
    
    turnSphereOn() {
      this.onSpheres.push(this.currentObj);
      this.currentObj.layers.set(1);
      // const prevMaxGain = this.maxGain;
      this.maxGain = 1 / (this.onSpheres.length + 1);
      this.updatePlaybackMode();
      this.showNeighbors(this.currentObj);
      
      this.currentObj.material.color.setHex(this.sphereOnColor);
      // this.renderer.render(this.scene, this.camera);
      this.render();
      this.currentObj = undefined;
    },
    
    turnSphereOff() {
      this.onSpheres.splice(this.onSpheres.indexOf(this.currentObj), 1);
      this.currentObj.material.color.setHex(this.hoverColor);
      this.currentObj.layers.set(0);
      const remains = this.onSpheres.filter(sphere => {
        return nestedInclude(this.currentObj.neighborPositions, this.getPosition(sphere))
      });
      const onSphereNeighbs = this.onSpheres.filter(sphere => sphere != this.currentObj).map(sphere => sphere.neighborPositions).flat();
      
      let neighbs = this.spheres.filter(sphere => nestedInclude(this.currentObj.neighborPositions, this.getPosition(sphere)));
      neighbs = neighbs.filter(sphere => ! remains.includes(sphere));
      neighbs = neighbs.filter(sphere => ! nestedInclude(onSphereNeighbs, this.getPosition(sphere)));
      neighbs.forEach(sphere => this.scene.remove(sphere));
      this.spheres = this.spheres.filter(sphere => sphere === this.currentObj || !neighbs.includes(sphere));
      if (this.spheres.includes(this.currentObj) && ! nestedInclude(onSphereNeighbs, this.getPosition(this.currentObj))) {
        if (this.spheres.length > 1) {
          this.scene.remove(this.currentObj);
          this.spheres.splice(this.onSpheres.indexOf(this.currentObj), 1)
        }
      }
      this.render();
    },
    
    render() {
      const center = this.getCenter();
      this.camera.position.x = this.initPosition[0];
      this.camera.position.y = this.initPosition[1];
      this.camera.position.z = this.initPosition[2];
      this.camera.translateX(center[0]);
      this.camera.translateY(center[1]);
      this.camera.translateZ(center[2]);
      this.camera.lookAt(...center);
      this.oldCenter = center;
      this.camera.move
      const removes = this.scene.children.filter(child => child.geometry && child.geometry.type === 'CylinderGeometry');
      removes.forEach(child => this.scene.remove(child));
      this.getConnections(this.spheres.map(sphere => this.getPosition(sphere)), 2);
      this.getConnections(this.onSpheres.map(sphere => this.getPosition(sphere)), 3);
      this.renderer.render(this.scene, this.camera);
    },
    
    getPosition(obj) {
      return [obj.position.x, obj.position.y, obj.position.z]
    },

    addSphere(x, y, z) {
      const geometry = new THREE.SphereGeometry(0.15, 8, 8);
      const material = new THREE.MeshPhongMaterial( {color: this.hoverColor, transparent: true} );
      const sphere = new THREE.Mesh( geometry, material );
      sphere.position.x = x;
      sphere.position.y = y;
      sphere.position.z = z;
      sphere.layers.set(0);
      this.scene.add( sphere );
      this.spheres.push(sphere);
      return sphere
    },

    addConnection(a, b, layer=undefined) {
      var geometry = new THREE.CylinderGeometry( 0.01, 0.01, 1, 4);
      var material = new THREE.MeshPhongMaterial( {color: 0x3461eb});
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
    },
  }
}
</script>



<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
body {
  margin: 0
}

#controls {
  z-index: 1;
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 500px;
  margin-top: 5px;
  margin-bottom: 5px;
  float: right;
  
  display: flex;
  flex-direction: column;
  align-content: flex-start;
  /* justify-content: center; */
  
  /* border: 1px solid blue; */
}

label {
  color: white;
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

</style>
