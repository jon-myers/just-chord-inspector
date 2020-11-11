class MyWorkletProcessor extends AudioWorkletProcessor {

  static get parameterDescriptors() {
    return [
      {
        name: 'phase',
        defaultValue: 0,
        max: 1,
        min: 0
      },
      {
        name: 'frequency',
        defaultValue: 200,
        min: Number.EPSILON
      }
    ];
  }
  constructor() {
    super();
    this.phase = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const output = outputs[0];

    const inputChannel0 = input[0];
    const outputChannel0 = output[0];

    const outlen = output[0].length;
    const freq = parameters.frequency.length === 1;
    const phase = parameters.phase.length === 1;

    for (let x = 0; x < outlen; x++) {
      const main = parameters.frequency[freq ? 0 : x] * x / sampleRate;
      outputChannel0[x] = Math.sin(
        (main + this.phase + parameters.phase[phase ? 0 : x]) * 2 * Math.PI
      )
    };

    this.phase += parameters.frequency[freq ? 0: outlen - 1] * outlen / sampleRate;
    this.phase %= sampleRate;


    // keep this processor alive.
    return true;
  }
}
registerProcessor('sineProcessor', MyWorkletProcessor);
