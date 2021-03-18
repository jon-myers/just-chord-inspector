require('worklet-loader');

module.exports = {
  publicPath: '/just-chord-inspector/',
  outputDir: 'dist',
  configureWebpack: {
    module: {
      rules: [
        {
          test: /Worklet\.js$/,
          loader: 'worklet-loader',
          options: {
            name: 'js/[hash].worklet.js'
          }
        }
      ]
    }
  }

}
