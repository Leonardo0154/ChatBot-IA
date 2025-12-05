const STORAGE_KEY = 'chatbot_session'

export function saveSession({ token, user }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, user }))
}

export function getSession() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (error) {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY)
}
