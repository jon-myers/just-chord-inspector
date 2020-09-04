// def encode(signal, theta, sigma):
//     """Encodes a mono signal as a first order ambisonic signal [4 channels] in
//     the AmbiX / ACN channel layout [w, y, z, x]."""
//     w = signal / (2**0.5)
//     x = signal * np.cos(theta) * np.cos(sigma)
//     y = signal * np.sin(theta) * np.cos(sigma)
//     z = signal * np.sin(sigma)
//     return np.array([w, y, z, x])



class MyWorkletProcessor extends AudioWorkletProcessor {

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
    // console.log(outputs)
    const w = outputs[0][0];
    const y = outputs[0][1];
    const z = outputs[0][2];
    const x = outputs[0][3]; 
    
    if (inputs[0].length != 0) {
      // const w = outputs[0][0];
      // const y = outputs[1][0];
      // const z = outputs[2][0];
      // const x = outputs[3][0]; 
      // // console.log(w)
      // console.log(inputs[0].length)
      const signal = inputs[0][0];
      // console.log(signal)
      for (let i = 0; i < 128; i++) {
        // console.log(signal[i])
        w[i] = signal[i] / (2 ** 0.5);
        x[i] = signal[i] * Math.cos(azimuth[i]) * Math.cos(elevation[i]);
        y[i] = signal[i] * Math.sin(azimuth[i]) * Math.cos(elevation[i]);
        z[i] = signal[i] * Math.sin(elevation[i]);
      }
        // console.log(outputs[0])
      
    }
    // console.log(outputs)
    // if (w) console.log(w)
    // keep this processor alive.
    return true;
  }
}
registerProcessor('monoEncode', MyWorkletProcessor);
