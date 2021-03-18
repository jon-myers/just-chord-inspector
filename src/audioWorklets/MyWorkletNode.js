export default class MyWorkletNode extends AudioWorkletNode {
   constructor(context) {
    super(context, 'monoEncode')
    console.log(this.channelCount)
  }
}
