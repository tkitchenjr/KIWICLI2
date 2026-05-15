import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

function DashboardPage() {
	const { user, logout } = useAuth()
	const [error, setError] = useState('')

	async function handleLogout() {
		setError('')

		try {
			await logout()
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Logout failed.')
		}
	}

	return (
		<main style={{ padding: '2rem' }}>
			<h1>Dashboard</h1>
			<p>You are logged in.</p>
			{user?.profile?.email && <p>Signed in as: {user.profile.email}</p>}

			{error && <p style={{ color: '#a94442' }}>{error}</p>}

			<button type="button" onClick={handleLogout} style={{ marginTop: '1rem' }}>
				Logout
			</button>
		</main>
	)
}

export default DashboardPage