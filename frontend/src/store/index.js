import { createStore } from 'vuex'
import chat from './modules/chat'
import document from './modules/document'
import app from './modules/app'
import auth from './modules/auth'
import dashboard from './modules/dashboard'

export default createStore({
  modules: {
    chat,
    document,
    app,
    auth,
    dashboard
  }
})
