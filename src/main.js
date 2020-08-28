import Vue from 'vue'
import App from './App.vue'
// import BaseIcon from './components/_base/BaseIcon.vue'

// Vue.config.performance = true;
// Vue.component('BaseIcon', BaseIcon)
Vue.config.productionTip = false


new Vue({
  render: h => h(App),
}).$mount('#app')
