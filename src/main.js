import Vue from 'vue'
import App from './App.vue'


Vue.config.performance = true;
Vue.config.productionTip = false

new Vue({
  render: h => h(App),
}).$mount('#app')
