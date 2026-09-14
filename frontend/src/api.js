const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export async function apiFetch(path, params = {}, signal) {
  const url = new URL(`${API_BASE_URL}${path}`)

  Object.entries(params).forEach(([key, value]) => {
    if (value == null || value === '' || (Array.isArray(value) && value.length === 0)) {
      return
    }
    if (Array.isArray(value)) {
      value.forEach((item) => url.searchParams.append(key, item))
      return
    }
    url.searchParams.set(key, value)
  })

  const response = await fetch(url, { signal })
  if (!response.ok) {
    const message = `Request failed with status ${response.status}`
    throw new Error(message)
  }
  return response.json()
}

export { API_BASE_URL }
