import {
	createContext,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useRef,
	useState,
} from 'react'
import {
	AuthProvider as ReactOidcAuthProvider,
	useAuth as useReactOidcAuth,
} from 'react-oidc-context'
import {
	cognitoAuthConfig,
	clearAuthStorage,
	getCognitoLogoutUrl,
	getMissingOidcConfig,
	getStoredToken,
	isOidcConfigured,
	isTokenExpired,
	persistToken,
} from '../services/auth'

const AppAuthContext = createContext(null)
const LOGOUT_FLAG_KEY = 'kiwi.logged_out'

const apiBaseUrlRaw = import.meta.env.VITE_API_BASE_URL || ''
const apiBaseUrl = apiBaseUrlRaw.replace(/\/+$/, '')

function shouldAttachToken(url) {
	if (url.startsWith(window.location.origin) || url.startsWith('/')) {
		return true
	}

	if (!apiBaseUrl) {
		return false
	}

	return url.startsWith(apiBaseUrl)
}

function toAbsoluteUrl(input) {
	if (typeof input === 'string') {
		return new URL(input, window.location.origin).toString()
	}

	if (input instanceof URL) {
		return input.toString()
	}

	if (input instanceof Request) {
		return input.url
	}

	return ''
}

function AppAuthStateProvider({ children }) {
	const oidc = useReactOidcAuth()
	const [user, setUser] = useState(null)
	const [token, setToken] = useState(null)
	const [isLoading, setIsLoading] = useState(true)

	const originalFetchRef = useRef(window.fetch.bind(window))

	const refreshAuthState = useCallback(async () => {
		if (!isOidcConfigured()) {
			setUser(null)
			setToken(null)
			setIsLoading(false)
			return null
		}

		if (oidc.isLoading || oidc.activeNavigator === 'signinRedirect') {
			setIsLoading(true)
			return null
		}

		const currentUser = oidc.user
		if (!currentUser?.id_token || isTokenExpired(currentUser.id_token)) {
			clearAuthStorage()
			void oidc.removeUser()
			setUser(null)
			setToken(null)
			setIsLoading(false)
			return null
		}

		persistToken(currentUser.id_token)
		setUser(currentUser)
		setToken(currentUser.id_token)
		setIsLoading(false)
		return currentUser
	}, [oidc])

	useEffect(() => {
		let ignore = false

		async function bootstrap() {
			try {
				const currentUser = await refreshAuthState()
				if (!currentUser && !ignore) {
					setUser(null)
					setToken(null)
				}
			} catch {
				if (!ignore) {
					clearAuthStorage()
					setUser(null)
					setToken(null)
					setIsLoading(false)
				}
			}
		}

		bootstrap()

		return () => {
			ignore = true
		}
	}, [refreshAuthState])

	useEffect(() => {
		window.fetch = async (input, init) => {
			const absoluteUrl = toAbsoluteUrl(input)
			const shouldHandle = absoluteUrl && shouldAttachToken(absoluteUrl)

			if (!shouldHandle) {
				return originalFetchRef.current(input, init)
			}

			const storedToken = getStoredToken()
			if (!storedToken || isTokenExpired(storedToken)) {
				clearAuthStorage()
				setUser(null)
				setToken(null)
				if (window.location.pathname !== '/login') {
					window.location.assign('/login')
				}
				throw new Error('Authentication required. Redirecting to login.')
			}

			const originalRequest =
				input instanceof Request ? input : new Request(input, init || {})
			const headers = new Headers(originalRequest.headers)
			headers.set('Authorization', `Bearer ${storedToken}`)

			const authenticatedRequest = new Request(originalRequest, {
				headers,
				body: init?.body,
			})

			return originalFetchRef.current(authenticatedRequest)
		}

		return () => {
			window.fetch = originalFetchRef.current
		}
	}, [])

	const startLogin = useCallback(async (returnTo = '/dashboard') => {
		await oidc.signinRedirect({ state: { returnTo } })
	}, [oidc])

	const completeCallback = useCallback(async () => {
		if (oidc.user?.id_token && !isTokenExpired(oidc.user.id_token)) {
			persistToken(oidc.user.id_token)
			setUser(oidc.user)
			setToken(oidc.user.id_token)
			return oidc.user
		}

		return null
	}, [oidc.user])

	const signOut = useCallback(async () => {
		const logoutUrl = getCognitoLogoutUrl()
		clearAuthStorage()
		await oidc.removeUser()
		setUser(null)
		setToken(null)
		window.sessionStorage.setItem(LOGOUT_FLAG_KEY, '1')

		if (logoutUrl) {
			window.location.assign(logoutUrl)
			return
		}

		window.location.assign('/login')
	}, [oidc])

	const value = useMemo(
		() => ({
			user,
			token,
			isLoading: isLoading || oidc.isLoading,
			isAuthenticated: Boolean(token && !isTokenExpired(token)),
			login: startLogin,
			logout: signOut,
			completeCallback,
			refreshAuthState,
			isOidcConfigured: isOidcConfigured(),
			error: oidc.error,
			missingConfig: getMissingOidcConfig(),
		}),
		[
			completeCallback,
			isLoading,
			oidc.error,
			oidc.isLoading,
			refreshAuthState,
			signOut,
			startLogin,
			token,
			user,
		],
	)

	return <AppAuthContext.Provider value={value}>{children}</AppAuthContext.Provider>
}

export function AuthProvider({ children }) {
	if (!isOidcConfigured()) {
		const value = {
			user: null,
			token: null,
			isLoading: false,
			isAuthenticated: false,
			login: async () => {},
			logout: async () => {},
			completeCallback: async () => null,
			refreshAuthState: async () => null,
			isOidcConfigured: false,
			error: null,
			missingConfig: getMissingOidcConfig(),
		}

		return <AppAuthContext.Provider value={value}>{children}</AppAuthContext.Provider>
	}

	return (
		<ReactOidcAuthProvider {...cognitoAuthConfig}>
			<AppAuthStateProvider>{children}</AppAuthStateProvider>
		</ReactOidcAuthProvider>
	)
}

export function useAuth() {
	const context = useContext(AppAuthContext)
	if (!context) {
		throw new Error('useAuth must be used within AuthProvider')
	}

	return context
}