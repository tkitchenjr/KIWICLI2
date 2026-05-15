import { clearAuthStorage, getStoredToken, isTokenExpired } from './auth'

const apiBaseUrlRaw = import.meta.env.VITE_API_BASE_URL || ''
const apiBaseUrl = apiBaseUrlRaw.replace(/\/+$/, '')

function buildUrl(path) {
	if (/^https?:\/\//i.test(path)) {
		return path
	}

	if (!apiBaseUrl) {
		return path
	}

	const normalizedPath = path.startsWith('/') ? path : `/${path}`
	return `${apiBaseUrl}${normalizedPath}`
}

function redirectToLoginIfNeeded() {
	if (window.location.pathname !== '/login') {
		window.location.assign('/login')
	}
}

function getAuthHeader() {
	const token = getStoredToken()
	if (!token || isTokenExpired(token)) {
		clearAuthStorage()
		redirectToLoginIfNeeded()
		throw new Error('Authentication required. Redirecting to login.')
	}

	return { Authorization: `Bearer ${token}` }
}

async function parseResponse(response) {
	const contentType = response.headers.get('content-type') || ''
	const isJson = contentType.includes('application/json')

	if (!response.ok) {
		let message = `Request failed with status ${response.status}`
		if (isJson) {
			try {
				const errorBody = await response.json()
				message = errorBody?.error || errorBody?.message || message
			} catch {
				// Keep fallback status message.
			}
		}
		throw new Error(message)
	}

	if (response.status === 204) {
		return null
	}

	if (!isJson) {
		return response.text()
	}

	return response.json()
}

export async function apiRequest(path, options = {}) {
	const {
		method = 'GET',
		body,
		headers = {},
		requiresAuth = true,
		credentials,
	} = options

	const requestHeaders = {
		Accept: 'application/json',
		...headers,
	}

	if (requiresAuth) {
		Object.assign(requestHeaders, getAuthHeader())
	}

	let payload = body
	if (body !== undefined && body !== null && !(body instanceof FormData)) {
		requestHeaders['Content-Type'] = requestHeaders['Content-Type'] || 'application/json'
		payload =
			typeof body === 'string' || requestHeaders['Content-Type'] !== 'application/json'
				? body
				: JSON.stringify(body)
	}

	const response = await fetch(buildUrl(path), {
		method,
		headers: requestHeaders,
		body: payload,
		credentials,
	})

	return parseResponse(response)
}

export function apiGet(path, options = {}) {
	return apiRequest(path, { ...options, method: 'GET' })
}

export function apiPost(path, body, options = {}) {
	return apiRequest(path, { ...options, method: 'POST', body })
}

export function apiPut(path, body, options = {}) {
	return apiRequest(path, { ...options, method: 'PUT', body })
}

export function apiPatch(path, body, options = {}) {
	return apiRequest(path, { ...options, method: 'PATCH', body })
}

export function apiDelete(path, options = {}) {
	return apiRequest(path, { ...options, method: 'DELETE' })
}
