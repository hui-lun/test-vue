<template>
  <div class="chat-app">
    <div class="chat-header">
      <div class="logo">
        <img src="/bdmchat-logo.png" alt="logo" />
        <span>BDM.CHAT</span>
      </div>
      <div class="header-icons">
        <span class="icon" @click="clearMessages" title="清除聊天紀錄">🗑️</span>
        <span class="icon">✉️</span>
        <span class="icon">👤</span>
        <!-- <span class="icon" @click="activateSearchSummarizeMode" title="自動搜尋與摘要">🔎</span> -->
      </div>
    </div>
    <div class="chat-body" ref="chatBody">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['msg-row', msg.sender]">
        <div :class="['msg-bubble', msg.sender]">
          <div v-if="msg.loading" class="loading-dots"><span></span><span></span><span></span></div>
          <div v-else v-html="msg.text"></div>
        </div>
      </div>
    </div>
        <form class="chat-footer" @submit.prevent="sendQuery">
      <input v-model="query" placeholder="請輸入訊息...." autocomplete="off" />
      <button type="submit">送出</button>
      <label style="display:flex;align-items:center;margin-left:12px;font-size:1.1em;gap:4px">
        <input type="checkbox" v-model="useAgent" style="width:22px;height:22px;accent-color:#1976d2;margin-right:4px" />
        啟用智能助理
      </label>
      <label style="display:flex;align-items:center;margin-left:12px;font-size:1.1em;gap:4px">
        <input type="checkbox" v-model="useSearchSummarizeMode" style="width:22px;height:22px;accent-color:#1976d2;margin-right:4px" />
        啟用搜尋與摘要模式
      </label>
    </form>

  </div>


</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import axios from 'axios'

const query = ref('')
const messages = ref([])
const useAgent = ref(false)


// 搜尋與摘要模式
const useSearchSummarizeMode = ref(false)


// 啟用自動搜尋與摘要模式
const activateSearchSummarizeMode = () => {
  useSearchSummarizeMode.value = true;
  messages.value.push({ sender: 'ai', text: '已啟用自動搜尋與摘要功能，請輸入您的問題' })
}

const clearMessages = () => {
  if (window.confirm('確定要刪除所有聊天紀錄嗎？')) {
    messages.value = []
  }
}

const chatBody = ref(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

const sendQuery = async () => {
  if (!query.value.trim()) return
  messages.value.push({ sender: 'user', text: query.value })
  const userMsg = query.value
  query.value = ''
  messages.value.push({ sender: 'ai', loading: true })
  try {
    let res
    if (useSearchSummarizeMode.value) {
      // 搜尋與摘要模式
      res = await axios.post('/search-and-summarize', { query: userMsg })
      messages.value[messages.value.length - 1] = { sender: 'ai', text: res.data.summary || JSON.stringify(res.data) }
    } else if (useAgent.value) {
      res = await axios.post('/agent-chat', { email_content: userMsg })
      messages.value[messages.value.length - 1] = { sender: 'ai', text: res.data.summary || JSON.stringify(res.data) }
    } else {
      res = await axios.post('/chat', { query: userMsg })
      // messages.value[messages.value.length - 1] = { sender: 'ai', text: res.data.response }
      messages.value[messages.value.length - 1] = { sender: 'ai', text: res.data.summary || JSON.stringify(res.data) }
    }
  } catch (e) {
    messages.value[messages.value.length - 1] = { sender: 'ai', text: 'Error: ' + (e.response?.data?.detail || e.message) }
  }
}
</script>

