import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function AuthCallbackPage() {
	const navigate = useNavigate()
	const { user, isAuthenticated, isLoading, error: authError } = useAuth()
	const [error, setError] = useState('')

	useEffect(() => {
		if (isLoading) {
			return
		}

		if (authError) {
			setError(authError.message)
			return
		}

		if (isAuthenticated) {
			const returnTo = user?.state?.returnTo || '/dashboard'
			navigate(returnTo, { replace: true })
			return
		}

		setError('Failed to complete Cognito sign-in callback.')
	}, [authError, isAuthenticated, isLoading, navigate, user])

	if (error) {
		return (
			<main style={{ padding: '2rem' }}>
				<h1>Authentication Failed</h1>
				<p>{error}</p>
			</main>
		)
	}

	return (
		<main style={{ padding: '2rem' }}>
			<h1>Finishing sign in...</h1>
			<p>Please wait while we complete your login.</p>
		</main>
	)
}

export default AuthCallbackPage
