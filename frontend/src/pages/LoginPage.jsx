import { useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import './LoginPage.css'
import { getMissingOidcConfig } from '../services/auth'
import { useAuth } from '../context/AuthContext'

const LOGOUT_FLAG_KEY = 'kiwi.logged_out'

function LoginPage() {
	const { login, isAuthenticated, isLoading, isOidcConfigured } = useAuth()
	const [error, setError] = useState('')
	const [loggedOut, setLoggedOut] = useState(false)
	const location = useLocation()

	const targetPath = useMemo(
		() => location.state?.from?.pathname || '/dashboard',
		[location.state],
	)

	useEffect(() => {
		const justLoggedOut = window.sessionStorage.getItem(LOGOUT_FLAG_KEY) === '1'
		if (justLoggedOut) {
			window.sessionStorage.removeItem(LOGOUT_FLAG_KEY)
			setLoggedOut(true)
		}
	}, [])

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
		<main className="login-shell">
			<section className="login-shell__brand">
				<div className="brand-content">
					<p className="brand-eyebrow">kiwi</p>
					<h1>Smart portfolio management for modern investors.</h1>
					<p>
						Track your holdings, execute trades, and review every transaction in one place.
					</p>
					<ul>
						<li>Create and manage multiple portfolios</li>
						<li>Buy and sell securities instantly</li>
						<li>Full transaction history with filters</li>
					</ul>
				</div>
			</section>

			<section className="login-shell__auth">
				<div className="auth-card" role="region" aria-label="Authentication">
					<h2>Welcome back</h2>
					<p>Sign in with AWS Cognito to access your portfolio dashboard.</p>

					{loggedOut && (
						<p className="auth-note">You have been signed out successfully.</p>
					)}

					{!isOidcConfigured && (
						<p className="auth-error">
							Missing OIDC config: {missingConfig.join(', ')}
						</p>
					)}

					{error && <p className="auth-error">Authentication error: {error}</p>}

					<button type="button" onClick={handleLogin} disabled={!isOidcConfigured}>
						Sign in with Kiwi
					</button>
				</div>
			</section>
		</main>
	)
}

export default LoginPage