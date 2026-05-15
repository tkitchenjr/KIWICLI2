import { useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getMissingOidcConfig } from '../services/auth'
import { useAuth } from '../context/AuthContext'

const LOGOUT_FLAG_KEY = 'kiwi.logged_out'

function LoginPage() {
	const { login, isAuthenticated, isLoading, isOidcConfigured } = useAuth()
	const [error, setError] = useState('')
	const redirectStartedRef = useRef(false)
	const location = useLocation()

	const targetPath = useMemo(
		() => location.state?.from?.pathname || '/dashboard',
		[location.state],
	)

	useEffect(() => {
		const justLoggedOut = window.sessionStorage.getItem(LOGOUT_FLAG_KEY) === '1'
		if (justLoggedOut) {
			window.sessionStorage.removeItem(LOGOUT_FLAG_KEY)
			return
		}

		if (isOidcConfigured && !redirectStartedRef.current) {
			redirectStartedRef.current = true
			void login(targetPath).catch((err) => {
				setError(err instanceof Error ? err.message : 'Unable to start sign in.')
				redirectStartedRef.current = false
			})
		}
	}, [isOidcConfigured, login, targetPath])

	if (isLoading) {
		return <main style={{ padding: '2rem' }}>Loading authentication state...</main>
	}

	if (isAuthenticated) {
		return <Navigate to={targetPath} replace />
	}

	async function handleLogin() {
		setError('')
		try {
			await login(targetPath)
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Unable to start sign in.')
		}
	}

	const missingConfig = getMissingOidcConfig()

	return (
		<main style={{ padding: '2rem' }}>
			<h1>Redirecting to Cognito...</h1>
			<p>Please wait while we redirect you to AWS Cognito Hosted UI.</p>

			{!isOidcConfigured && (
				<p style={{ color: '#a94442', marginTop: '1rem' }}>
					Missing OIDC config: {missingConfig.join(', ')}
				</p>
			)}

			{error && (
				<p style={{ color: '#a94442', marginTop: '1rem' }}>
					Authentication error: {error}
				</p>
			)}

			<button
				type="button"
				onClick={handleLogin}
				style={{ marginTop: '1rem' }}
				disabled={!isOidcConfigured}
			>
				Retry Redirect
			</button>
		</main>
	)
}

export default LoginPage