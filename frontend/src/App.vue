<template>
  <div class="chat-app">
    <div class="chat-header">
      <div class="logo">
        <!-- <img src="/bdmchat-logo.png" alt="logo" /> -->
        <span>BDM.Agent</span>
      </div>
      <div class="header-icons">
        <span class="icon" @click="clearMessages" title="清除聊天紀錄">🗑️</span>
        <span class="icon" @click="sendEmailContent" title="傳入信件內容">✉️</span>
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
    </form>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import axios from 'axios'

const query = ref('')
const messages = ref([])


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
    //const res = await axios.post('http://192.168.1.193:8000/chat', { query: userMsg })
    const res = await axios.post('/chat', { query: userMsg })
    messages.value[messages.value.length - 1] = { sender: 'ai', text: res.data.response }
  } catch (e) {
    messages.value[messages.value.length - 1] = { sender: 'ai', text: 'Error: ' + e.message }
  }
}

const sendEmailContent = () => {
  if (typeof Office === 'undefined') {
    alert("目前不在 Outlook 增益集環境，無法讀取郵件內容");
    return;
  }

  Office.onReady(() => {
    if (Office.context.mailbox && Office.context.mailbox.item) {
      Office.context.mailbox.item.body.getAsync("text", (result) => {
        if (result.status === Office.AsyncResultStatus.Succeeded) {
          const content = result.value.trim();
          if (content) {
            query.value = content;
            sendQuery(content);
          } else {
            alert("這封信內容為空白");
          }
        } else {
          alert("無法取得信件內容");
          console.error("getAsync error:", result.error);
        }
      });
    } else {
      alert("無法存取信件物件");
    }
  });
};


</script>

