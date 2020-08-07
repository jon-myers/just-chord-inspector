<template>
  <div class="hello" @mousemove='mouseMove'>
    <canvas ref='canvas'></canvas>
  </div>
</template>

<script>
const THREE = require('three');

const AudioContext = window.AudioContext || window.webkitAudioContext;

const inclusiveRange = (start, end) => {
  return [...Array((end+1) - start).keys()].map(i => i + start)
}
export default {
  name: 'JustPlot',
  data() {
    return {
      gridColor: 0x6c6e73,
      sphereColor: 0x3461eb,
      hoverColor: 0xffff00,
      spheres: [],
      currentObj: undefined,
      fund: 100,
      slewTime: 0.1,
    }
  },
  mounted() {
    this.setUpAudio();
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );
    // this.camera = new THREE.OrthographicCamera(-10, 10, -10, 10, -10, 100)
    
    // this.projector = new THREE.Projector();
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    
    
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.$refs.canvas
    });
    this.renderer.setSize( window.innerWidth, window.innerHeight );
    
    const cubeSize = [4, 3, 2];
    const points = [];
    
    for (let x = 0; x < cubeSize[0]; x++) {
      for (let y = 0; y < cubeSize[1]; y++) {
        for (let z = 0; z < cubeSize[2]; z++) {
          points.push([x, y, z])
        }
      }
    }
    
    // const points = [
    //   [0, 0, 0],
    //   [0, 0, 1],
    //   [0, 1, 0],
    //   [1, 0, 0],
    //   [0, 1, 1],
    //   [1, 0, 1], 
    //   [1, 1, 0],
    //   [1, 1, 1]  
    // ]
    
    this.drawPoints(points);
    
    // this.addGrid(2, 2, 2)
    
    var light = new THREE.HemisphereLight( 0xffffbb, 0x080820, 1 );
    this.scene.add( light );

    this.camera.position.z = 5;
    this.camera.position.x = 3;
    this.camera.position.y = 3
    this.camera.lookAt(0, 0, 0);
    // this.animate()
    
    this.renderer.render(this.scene, this.camera);
  },

  methods: {
    
    drawPoints(points) {
      points.forEach(point => this.addSphere(...point))
      this.getConnections(points)
    },
    
    getConnections(points) {
      let combinations = points.flatMap(
        (v, i) => points.slice(i + 1).map(w => [v, w])
      );
      combinations = combinations.filter(comb => {
        const dist = [0, 1, 2].map(i => comb[1][i] - comb[0][i]).filter(num => num != 0);
        return dist.length === 1 && Math.abs(dist[0]) === 1
      });
      combinations.forEach(comb => {
        this.addConnection(...comb)
      })
    },
    
    setUpAudio() {
      this.ac = new AudioContext();
      this.masterGain = this.ac.createGain();
      
      this.masterGain.gain.setValueAtTime(0.5, this.ac.currentTime);
      
      this.masterGain.connect(this.ac.destination);
    },
    
    startNote(obj) {
      const pos = [obj.position.x, obj.position.y, obj.position.z];
      const primes = [3, 5, 7];
      let freq = this.fund * pos.map((p, i) => primes[i]**p).reduce((a, b) => a * b, 1);
      while (freq > 400) freq /= 2;
      while (freq < 200) freq *= 2;
      obj.osc = this.ac.createOscillator();
      obj.osc.type = 'triangle';
      obj.gainNode = this.ac.createGain();
      obj.osc.frequency.setValueAtTime(freq, this.ac.currentTime);
      obj.gainNode.gain.setValueAtTime(0, this.ac.currentTime);
      obj.gainNode.gain.linearRampToValueAtTime(1, this.ac.currentTime + this.slewTime);
      obj.osc.connect(obj.gainNode);
      obj.gainNode.connect(this.masterGain);
      obj.osc.start();
    },
    
    stopNote(obj) {
      console.log('stop note');
      obj.gainNode.gain.setValueAtTime(1, this.ac.currentTime);
      obj.gainNode.gain.linearRampToValueAtTime(0, this.ac.currentTime + this.slewTime);
      obj.osc.stop(this.ac.currentTime + this.slewTime);
      obj.osc = undefined;
    },
    
    hoverOverSphere(obj) {
      if (obj != this.currentObj) {
        if (this.currentObj) {
          this.currentObj.material.color.setHex(this.sphereColor);
          if (this.currentObj.osc) this.stopNote(this.currentObj);
        }
        this.currentObj = obj
      }
      if (this.ac.state === 'suspended') this.ac.resume();
      if (!obj.osc) this.startNote(obj);
      obj.material.color.setHex(this.hoverColor);
      this.renderer.render(this.scene, this.camera);
    },
    
    mouseMove(e) {
      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = (1 - e.clientY / window.innerHeight) * 2 - 1;
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObjects(this.spheres);
      if (intersects[0]) {
        this.hoverOverSphere(intersects[0].object);
      } else {
        if (this.currentObj && this.currentObj.material.color.getHex() != this.sphereColor) {
          this.currentObj.material.color.setHex(this.sphereColor);
          this.stopNote(this.currentObj);
          this.renderer.render(this.scene, this.camera);
          
        }
        
      }
    },
    
    // update() {
    //   this.raycaster.setFromCamera(this.mouse, this.camera);
    //   const intersects = this.rayCaster.intersectObjects(this.scene.children);
    //   console.log(intersects)
    // },
    
    animate() {
      requestAnimationFrame(this.animate);
      this.renderer.render(this.scene, this.camera);
    },

    addSphere(x, y, z) {
      const geometry = new THREE.SphereGeometry(0.25, 32, 32);
      const material = new THREE.MeshPhongMaterial( {color: this.sphereColor} );
      const sphere = new THREE.Mesh( geometry, material );
      sphere.position.x = x
      sphere.position.y = y
      sphere.position.z = z
      this.scene.add( sphere );
      this.spheres.push(sphere);
    },

    addConnection(a, b) {
      var geometry = new THREE.CylinderGeometry( 0.03, 0.03, 1, 32);
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
      this.scene.add(cylinder);
    },
    
    // centered at origin, distance from origin to edge, not edge to edge
    addGrid(x, y, z) {
      const geoX = new THREE.CylinderGeometry( 0.01, 0.01, 2 * x, 32);
      const geoY = new THREE.CylinderGeometry( 0.01, 0.01, 2 * y, 32);
      const geoZ = new THREE.CylinderGeometry( 0.01, 0.01, 2 * z, 32);
      // const geoZ = new THREE.CylinderGeometry( 0.03, 0.03, z + 1, 32);
      const material = new THREE.MeshPhongMaterial( {
        color: this.gridColor,
        transparent: true,
        opacity: 0.4
      })
      
      inclusiveRange(-x, x).forEach(x => {
        inclusiveRange(-y, y).forEach(y => {
          const cylinder = new THREE.Mesh(geoZ, material);
          cylinder.position.x = x
          cylinder.position.y = y
          cylinder.position.z = 0
          cylinder.rotateX(Math.PI / 2)
          this.scene.add(cylinder);  
        })
      })
      
      inclusiveRange(-y, y).forEach(y => {
        inclusiveRange(-z, z).forEach(z => {
          const cylinder = new THREE.Mesh(geoX, material);
          cylinder.position.x = 0
          cylinder.position.y = y
          cylinder.position.z = z
          cylinder.rotateZ(Math.PI / 2)
          this.scene.add(cylinder);  
        })
      })
      
      inclusiveRange(-z, z).forEach(z => {
        inclusiveRange(-x, x).forEach(x => {
          const cylinder = new THREE.Mesh(geoY, material);
          cylinder.position.x = x
          cylinder.position.y = 0
          cylinder.position.z = z
          this.scene.add(cylinder);  
        })
      })
      
      // var material = new THREE.MeshPhongMaterial( {color: 0x3461eb});
    }
  }
}
</script>



<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
body {
  margin: 0
}

</style>
