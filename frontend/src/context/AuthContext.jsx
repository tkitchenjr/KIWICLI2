import {
	createContext,
	useCallback,
	useContext,
	useEffect,
	useMemo,
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
	isOidcConfigured,
	isTokenExpired,
	persistToken,
} from '../services/auth'

const AppAuthContext = createContext(null)
const LOGOUT_FLAG_KEY = 'kiwi.logged_out'

function AppAuthStateProvider({ children }) {
	const oidc = useReactOidcAuth()
	const [user, setUser] = useState(null)
	const [token, setToken] = useState(null)
	const [isLoading, setIsLoading] = useState(true)

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
		if (!currentUser?.access_token || isTokenExpired(currentUser.access_token)) {
			clearAuthStorage()
			void oidc.removeUser()
			setUser(null)
			setToken(null)
			setIsLoading(false)
			return null
		}

		persistToken(currentUser.access_token)
		setUser(currentUser)
		setToken(currentUser.access_token)
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

	const startLogin = useCallback(async (returnTo = '/dashboard') => {
		await oidc.signinRedirect({ state: { returnTo } })
	}, [oidc])

	const completeCallback = useCallback(async () => {
		if (oidc.user?.access_token && !isTokenExpired(oidc.user.access_token)) {
			persistToken(oidc.user.access_token)
			setUser(oidc.user)
			setToken(oidc.user.access_token)
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

		window.location.assign('/')
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