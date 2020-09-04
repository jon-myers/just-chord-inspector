
class MyWorkletProcessor extends AudioWorkletProcessor {
  
  // Encodes a mono signal as an ambisonic B-format arriving from a given direction.
  // Takes an input signal, azimuth and elevation angles (both in radians), and 
  // returns a 4-channel first order ambisonic signal in the FUMA format. 

  static get parameterDescriptors() {
    return [
      {
        name: 'azimuth',
        defaultValue: 0,
        min: -Math.PI,
        max: Math.PI,
      },
      {
        name: 'elevation',
        defaultValue: 0,
        min: -Math.PI / 2,
        max: Math.PI / 2,
      }
    ];
  }
  constructor() {
    super();


  }

  process(inputs, outputs, parameters) {
    // console.log(outputs[1])
    let azimuth = parameters.azimuth.length == 1 ? Array(128).fill(parameters.azimuth[0]) : parameters.azimuth;
    let elevation = parameters.elevation.length == 1 ? Array(128).fill(parameters.elevation[0]) : parameters.elevation;

    // fuma B-format ambisonic ordering; (not ambiX)
    const w = outputs[0][0];
    const y = outputs[0][1];
    const z = outputs[0][2];
    const x = outputs[0][3]; 
    if (inputs[0].length != 0) {
      const signal = inputs[0][0];
      for (let i = 0; i < 128; i++) {
        w[i] = signal[i] / (2 ** 0.5);
        x[i] = signal[i] * Math.cos(azimuth[i]) * Math.cos(elevation[i]);
        y[i] = signal[i] * Math.sin(azimuth[i]) * Math.cos(elevation[i]);
        z[i] = signal[i] * Math.sin(elevation[i]);
      }      
    }

    // keep this processor alive
    return true;
  }
}
registerProcessor('monoEncode', MyWorkletProcessor);
