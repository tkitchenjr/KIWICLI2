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
	if (window.location.pathname !== '/') {
		window.location.assign('/')
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
				const base = errorBody?.error || errorBody?.message
				const detail = errorBody?.detail
				if (base && detail) {
					message = `${base}: ${detail}`
				} else {
					message = base || detail || message
				}
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

// Portfolio API functions
export async function getPortfoliosByUser(username) {
	return apiGet(`/portfolios/user/${encodeURIComponent(username)}`)
}

export async function createPortfolio(name, description, username) {
	return apiPost('/portfolios/', { name, description, username })
}

export async function deletePortfolio(portfolioId) {
	return apiDelete(`/portfolios/${portfolioId}`)
}

export async function getPortfolioById(portfolioId) {
	return apiGet(`/portfolios/${portfolioId}`)
}

export async function getPortfolioTransactions(portfolioId) {
	return apiGet(`/portfolios/${portfolioId}/transactions`)
}

// User API functions
export async function ensureCurrentUser() {
	return apiPost('/users/me/ensure', {})
}

// Trading API functions
export async function executeBuyOrder(portfolioId, ticker, quantity) {
	return apiPost('/trades/buy', {
		portfolio_id: portfolioId,
		ticker,
		quantity,
	})
}

export async function executeSellOrder(portfolioId, ticker, quantity) {
	return apiPost('/trades/sell', {
		portfolio_id: portfolioId,
		ticker,
		quantity,
	})
}
