import { WebStorageStateStore } from 'oidc-client-ts'

const STORAGE_TOKEN_KEY = 'kiwi.id_token'
const STORAGE_USER_KEY_PREFIX = 'oidc.user:'

const authorityInput = import.meta.env.VITE_COGNITO_AUTHORITY
const region = import.meta.env.VITE_COGNITO_REGION
const userPoolId =
	import.meta.env.VITE_COGNITO_USER_POOL_ID ||
	import.meta.env.VITE_COGNITO_POOL_ID
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID
const cognitoDomainInput = import.meta.env.VITE_COGNITO_DOMAIN

const cognitoDomain = normalizeDomain(cognitoDomainInput)

const redirectUri =
	import.meta.env.VITE_COGNITO_REDIRECT_URI ||
	`${window.location.origin}/callback`
const postLogoutRedirectUri =
	import.meta.env.VITE_COGNITO_LOGOUT_REDIRECT_URI ||
	`${window.location.origin}/login`

const authority =
	authorityInput ||
	(region && userPoolId
		? `https://cognito-idp.${region}.amazonaws.com/${userPoolId}`
		: '')

const isConfigured = Boolean(authority && clientId && cognitoDomain)

export const cognitoAuthConfig = {
	authority,
	client_id: clientId,
	redirect_uri: redirectUri,
	response_type: 'code',
	scope:
		import.meta.env.VITE_COGNITO_SCOPE ||
		'aws.cognito.signin.user.admin email openid profile',
	metadata: {
		issuer: authority,
		authorization_endpoint: `${cognitoDomain}/oauth2/authorize`,
		token_endpoint: `${cognitoDomain}/oauth2/token`,
		userinfo_endpoint: `${cognitoDomain}/oauth2/userInfo`,
		end_session_endpoint: `${cognitoDomain}/logout`,
		jwks_uri: `${authority}/.well-known/jwks.json`,
	},
	userStore: new WebStorageStateStore({ store: window.localStorage }),
}

function normalizeDomain(domain) {
	if (!domain) {
		return ''
	}

	const trimmed = domain.replace(/\/+$/, '')
	return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`
}

function decodeJwtPayload(token) {
	try {
		const payload = token.split('.')[1]
		if (!payload) {
			return null
		}

		const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
		const base64 = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
		return JSON.parse(window.atob(base64))
	} catch {
		return null
	}
}

export function getPostLogoutRedirectUri() {
	return postLogoutRedirectUri
}

export function getCognitoLogoutUrl() {
	if (!cognitoDomain || !clientId) {
		return ''
	}

	return `${cognitoDomain}/logout?client_id=${encodeURIComponent(clientId)}&logout_uri=${encodeURIComponent(postLogoutRedirectUri)}`
}

export function isOidcConfigured() {
	return isConfigured
}

export function getMissingOidcConfig() {
	const missing = []

	if (!authorityInput && !(region && userPoolId)) {
		missing.push(
			'VITE_COGNITO_AUTHORITY (or VITE_COGNITO_REGION + VITE_COGNITO_USER_POOL_ID/VITE_COGNITO_POOL_ID)',
		)
	}
	if (!cognitoDomainInput) missing.push('VITE_COGNITO_DOMAIN')
	if (!clientId) missing.push('VITE_COGNITO_CLIENT_ID')

	return missing
}

export function getStoredToken() {
	return window.localStorage.getItem(STORAGE_TOKEN_KEY)
}

export function persistToken(token) {
	if (!token) {
		return
	}

	window.localStorage.setItem(STORAGE_TOKEN_KEY, token)
}

export function clearAuthStorage() {
	window.localStorage.removeItem(STORAGE_TOKEN_KEY)

	Object.keys(window.localStorage)
		.filter(
			(key) => key.startsWith(STORAGE_USER_KEY_PREFIX) || key.startsWith('oidc.'),
		)
		.forEach((key) => window.localStorage.removeItem(key))

	// OIDC signin state records are commonly stored in sessionStorage.
	Object.keys(window.sessionStorage)
		.filter((key) => key.startsWith('oidc.'))
		.forEach((key) => window.sessionStorage.removeItem(key))
}

export function isTokenExpired(token, clockSkewSeconds = 30) {
	if (!token) {
		return true
	}

	const payload = decodeJwtPayload(token)
	if (!payload?.exp) {
		return true
	}

	const nowSeconds = Math.floor(Date.now() / 1000)
	return payload.exp <= nowSeconds + clockSkewSeconds
}