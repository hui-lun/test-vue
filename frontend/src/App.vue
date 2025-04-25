<template>
  <div class="chat-app">
    <!-- 遮罩 -->
    <div v-if="showHistoryMenu" class="drawer-mask" @click="closeHistoryMenu"></div>
    <!-- 歷史紀錄抽屜 -->
    <aside class="history-drawer" :class="{ open: showHistoryMenu }">
      <div class="drawer-header">
        <span>歷史紀錄</span>
        <span class="close-btn" @click="closeHistoryMenu">×</span>
      </div>
      <ul class="drawer-list">
        <li v-for="(item, idx) in chatHistory" :key="idx"
            :class="['drawer-item', { selected: idx === selectedHistoryIdx }]"
            @click="selectHistory(idx)">
          <template v-if="editIdx !== idx">
  <div class="drawer-item-left">
    <span class="drawer-title">{{ item.title }}</span>
  </div>
  <div class="drawer-item-right">
    <span class="drawer-time">{{ item.time }}</span>
    <span class="drawer-menu-btn" @click.stop="toggleMenu(idx)">⋯</span>
    <div v-if="menuIdx === idx" class="drawer-menu-popup" @click.stop>
      <div class="drawer-menu-item" @click.stop="startRename(idx, item.title)">重新命名</div>
      <div class="drawer-menu-item danger" @click.stop="openDeleteModal(idx)">刪除</div>
    </div>
  </div>
</template>
          <template v-else>
            <input class="drawer-rename-input" v-model="renameTitle" ref="renameInput" @keyup.enter="finishRename(idx)" @blur="finishRename(idx)" />
          </template>
        </li>
        <li v-if="!chatHistory.length" class="drawer-empty">尚無歷史紀錄</li>
      </ul>
    </aside>

    <!-- 刪除確認 Popover -->
    <teleport to="body">
      <div v-if="showDeleteModal && deletePopoverPos" class="delete-popover-mask" @click="closeDeleteModal">
        <div class="delete-popover" :style="deletePopoverStyle" @click.stop>
          <div class="delete-popover-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="12" fill="#ffeaea"/><path d="M9.5 11v4m5-4v4M5 7h14m-2 0-.545 9.26A2 2 0 0 1 14.46 18h-4.92a2 2 0 0 1-1.995-1.74L5 7Zm3-2h4a1 1 0 0 1 1 1v1H7V6a1 1 0 0 1 1-1Z" stroke="#e74c3c" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div class="delete-popover-title">確定要刪除此聊天紀錄嗎？</div>
          <div class="delete-popover-actions">
            <button class="delete-popover-btn danger" @click="doDeleteHistory">確定</button>
            <button class="delete-popover-btn" @click="closeDeleteModal">取消</button>
          </div>
        </div>
      </div>
    </teleport>

    <div class="chat-header">
      <div class="logo">
        <!-- <img src="/bdmchat-logo.png" alt="logo" /> -->
        <span>BDM.Agent</span>
      </div>
      <div class="header-icons">
        <span class="icon" @click="openHistoryMenu" title="聊天歷史紀錄">🕑</span>
        <!-- <span class="icon" @click="clearMessages" title="清除聊天紀錄">🗑️</span> -->
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
import { ref, nextTick, watch, onMounted, computed } from 'vue'
import axios from 'axios'

const query = ref('')
const messages = ref([])

// 歷史紀錄抽屜狀態與資料
const showHistoryMenu = ref(false)
const selectedHistoryIdx = ref(null)
const chatHistory = ref([
  { title: '2024-04-25 上午對話', time: '09:21', messages: [
    { sender: 'user', text: '你好' }, { sender: 'ai', text: '哈囉！有什麼可以幫您？' }
  ] },
  { title: '2024-04-24 下午對話', time: '15:02', messages: [
    { sender: 'user', text: '今天天氣？' }, { sender: 'ai', text: '晴時多雲' }
  ] }
])

// menu 與 rename 狀態
const menuIdx = ref(null) // 哪個 menu 展開
const editIdx = ref(null) // 哪個在 rename
const renameTitle = ref('')
const renameInput = ref(null)

function openHistoryMenu() {
  showHistoryMenu.value = true
  closeMenu()
}
function closeHistoryMenu() {
  showHistoryMenu.value = false
  closeMenu()
}
function selectHistory(idx) {
  if (editIdx.value !== null || menuIdx.value !== null) return
  messages.value = [...chatHistory.value[idx].messages]
  selectedHistoryIdx.value = idx
  closeHistoryMenu()
}
function toggleMenu(idx) {
  menuIdx.value = menuIdx.value === idx ? null : idx
  editIdx.value = null
}
function closeMenu() {
  menuIdx.value = null
  editIdx.value = null
}
function startRename(idx, title) {
  editIdx.value = idx
  menuIdx.value = null
  renameTitle.value = title
  nextTick(() => {
    if (renameInput.value) renameInput.value.focus()
  })
}
function finishRename(idx) {
  const val = renameTitle.value.trim()
  if (val) chatHistory.value[idx].title = val
  editIdx.value = null
}
const showDeleteModal = ref(false)
const deletePopoverPos = ref(null)
let pendingDeleteIdx = null
function openDeleteModal(idx) {
  menuIdx.value = null
  nextTick(() => {
    // 找到當前 drawer-item 的 DOM
    const items = document.querySelectorAll('.drawer-item')
    const el = items[idx]
    if (el) {
      const rect = el.getBoundingClientRect()
      deletePopoverPos.value = {
        top: rect.top + rect.height/2 + window.scrollY,
        left: rect.right + 8 + window.scrollX
      }
    } else {
      deletePopoverPos.value = null
    }
    showDeleteModal.value = true
    pendingDeleteIdx = idx
  })
}
function closeDeleteModal() {
  showDeleteModal.value = false
  deletePopoverPos.value = null
  pendingDeleteIdx = null
}
function doDeleteHistory() {
  if (pendingDeleteIdx !== null) {
    chatHistory.value.splice(pendingDeleteIdx, 1)
    if (selectedHistoryIdx.value === pendingDeleteIdx) selectedHistoryIdx.value = null
    closeDeleteModal()
  }
}
const deletePopoverStyle = computed(() => {
  if (!deletePopoverPos.value) return {}
  return {
    position: 'absolute',
    top: deletePopoverPos.value.top + 'px',
    left: deletePopoverPos.value.left + 'px',
    zIndex: 3000
  }
})
// 點擊抽屜以外自動關閉 menu/input
onMounted(() => {
  document.addEventListener('click', closeMenuOnOutside)
})
function closeMenuOnOutside(e) {
  const drawer = document.querySelector('.history-drawer')
  if (drawer && !drawer.contains(e.target)) closeMenu()
}


// const clearMessages = () => {
//   if (window.confirm('確定要刪除所有聊天紀錄嗎？')) {
//     messages.value = []
//   }
// }

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

// 共用函式：從信件中讀取內容並送出
const handleEmailChange = () => {
  if (Office.context.mailbox?.item) {
    Office.context.mailbox.item.body.getAsync("text", (result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        const content = result.value.trim()
        if (content) {
          query.value = content
          // sendQuery(content)
        } else {
          alert("這封信內容為空白")
        }
      } else {
        alert("無法取得信件內容")
        console.error("getAsync error:", result.error)
      }
    })
  } else {
    alert("無法存取信件物件")
  }
}

// 觸發按鈕
const sendEmailContent = () => {
  if (typeof Office === 'undefined' || !Office.context.mailbox?.item) {
    alert("目前不在 Outlook 增益集環境，無法讀取郵件內容")
    return
  }
  handleEmailChange()
}


// 自動監聽信件切換（Taskpane 被 Pin 時）
onMounted(() => {
  if (typeof Office === 'undefined') return

  Office.onReady().then(() => {
    // 自動監聽 pin 狀態下的信件變更
    Office.context.mailbox.addHandlerAsync(
      Office.EventType.ItemChanged,
      handleEmailChange
    )
  })
})



</script>

