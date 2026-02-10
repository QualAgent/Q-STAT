<template>
  <div>
    <h1>Q-STAT Dev Environment Check</h1>
    <hr />

    <section>
      <h2>1. Backend Health</h2>
      <p :style="{ color: health.status === 'ok' ? 'green' : 'red' }">
        {{ health.status === 'ok' ? 'Backend Connected' : 'Backend Unreachable' }}
      </p>
    </section>

    <section>
      <h2>2. Environment</h2>
      <ul>
        <li>
          LangGraph:
          <span v-if="env.langgraph?.status === 'ok'">v{{ env.langgraph.version }}</span>
          <span v-else style="color: red">Not found</span>
        </li>
        <li>
          OpenAI API Key:
          <span :style="{ color: env.openai_api_key?.status === 'ok' ? 'green' : 'red' }">
            {{ env.openai_api_key?.status === 'ok' ? 'Loaded' : 'Missing' }}
          </span>
        </li>
      </ul>
    </section>

    <section>
      <h2>3. Database Connection</h2>
      <p v-if="db.status === 'ok'" style="color: green">PostgreSQL Connected</p>
      <p v-else style="color: red">{{ db.detail || 'DB Connection Failed' }}</p>
      <code v-if="db.version">{{ db.version }}</code>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const health = ref({})
const env = ref({})
const db = ref({})

async function fetchJson(url) {
  try {
    const res = await fetch(url)
    return await res.json()
  } catch {
    return { status: 'error' }
  }
}

onMounted(async () => {
  health.value = await fetchJson('/api/health')
  env.value = await fetchJson('/api/check/env')
  db.value = await fetchJson('/api/check/db')
})
</script>
