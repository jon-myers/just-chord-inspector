<template>
  <div class="hello">
    <canvas ref='canvas'></canvas>
  </div>
</template>

<script>
const THREE = require('three')
export default {
  name: 'JustPlot',
  mounted() {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.$refs.canvas
    });
    this.renderer.setSize( window.innerWidth, window.innerHeight );

    // document.body.appendChild( this.renderer.domElement );

    // this.addSphere(-1, 0, 0)
    // this.addSphere(-1, 0, 1)
    // this.addSphere(-1, 1, 0)
    // this.addSphere(-1, 1, 1)
    // this.addSphere(0, 0, 0)
    // this.addSphere(0, 0, 1)
    // this.addSphere(0, 1, 0)
    // this.addSphere(0, 1, 1)
    // this.addSphere(1, 0, 0)
    // this.addSphere(1, 0, 1)
    // this.addSphere(1, 1, 0)
    // this.addSphere(1, 1, 1)

    const pointA = [-1, 0, 0];
    const pointB = [-1, 0, 1];
    this.addSphere(...pointA);
    this.addSphere(...pointB);

    this.addConnection(pointA, pointB);


    var light = new THREE.HemisphereLight( 0xffffbb, 0x080820, 1 );
    this.scene.add( light );

    this.camera.position.z = 8;
    this.camera.position.x = 3;
    this.camera.position.y = 3
    this.animate()


  },

  methods: {

    animate() {
      requestAnimationFrame(this.animate);
      this.renderer.render(this.scene, this.camera);
    },

    addSphere(x, y, z) {
      const geometry = new THREE.SphereGeometry(0.25, 32, 32);
      const material = new THREE.MeshPhongMaterial( {color: 0xffff00} );
      const sphere = new THREE.Mesh( geometry, material );
      sphere.position.x = x
      sphere.position.y = y
      sphere.position.z = z
      this.scene.add( sphere );
    },

    addConnection(a, b) {
      var geometry = new THREE.CylinderGeometry( 0.1, 0.1, 1, 32);
      var material = new THREE.MeshPhongMaterial( {color: 0x83483C});
      const cylinder = new THREE.Mesh( geometry, material );
      cylinder.position.x = (a[0] + b[0]) / 2;
      cylinder.position.y = (a[1] + b[1]) / 2;
      cylinder.position.z = (a[2] + b[2]) / 2;
      this.scene.add(cylinder);
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
