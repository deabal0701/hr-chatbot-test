import { createStore } from 'vuex'
import chat from './modules/chat'
import document from './modules/document'
import app from './modules/app'

export default createStore({
  modules: {
    chat,
    document,
    app
  }
})
