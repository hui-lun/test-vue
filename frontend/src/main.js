import './assets/style.css'
import { createApp } from 'vue'
import App from './App.vue'

Office.onReady().then(() => {
    createApp(App).mount('#app')
})
