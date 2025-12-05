const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '')

async function request(path, { method = 'GET', body, token, headers = {}, isForm = false } = {}) {
  const config = { method, headers: new Headers(headers) }

  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }

  if (body !== undefined && body !== null) {
    if (isForm) {
      config.headers.set('Content-Type', 'application/x-www-form-urlencoded')
      config.body = body
    } else {
      config.headers.set('Content-Type', 'application/json')
      config.body = typeof body === 'string' ? body : JSON.stringify(body)
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, config)
  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : await response.text()

  if (!response.ok) {
    const detail = payload?.detail || payload?.message || payload || 'Error desconocido'
    const error = new Error(typeof detail === 'string' ? detail : 'Error en la solicitud')
    error.status = response.status
    error.payload = payload
    throw error
  }

  return payload
}

export async function login(username, password) {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  return request('/token', { method: 'POST', body: params, isForm: true })
}

export function registerUser(payload) {
  return request('/users/', { method: 'POST', body: payload })
}

export function fetchProfile(token) {
  return request('/users/me/', { token })
}

export function processSentence(token, text) {
  return request('/process', { method: 'POST', token, body: { text } })
}

export function logoutUser(token) {
  return request('/logout', { method: 'POST', token })
}

export { API_BASE_URL }
