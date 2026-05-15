import { useEffect, useState } from 'react'
import AppNavbar from '../components/layout/AppNavbar'
import PortfolioList from '../components/portfolios/PortfolioList'
import CreatePortfolioModal from '../components/portfolios/CreatePortfolioModal'
import { useAuth } from '../context/AuthContext'
import { getPortfoliosByUser, ensureCurrentUser } from '../services/api'

function DashboardPage() {
	const { user, logout } = useAuth()
	const [error, setError] = useState('')
	const [portfolios, setPortfolios] = useState([])
	const [loading, setLoading] = useState(true)
	const [portfolioError, setPortfolioError] = useState('')
	const [isModalOpen, setIsModalOpen] = useState(false)
	const [accountUsername, setAccountUsername] = useState('')

	// Extract username from OIDC user profile
	const fallbackUsername =
		user?.profile?.preferred_username ||
		user?.profile?.['cognito:username'] ||
		user?.profile?.email ||
		''

	// Fetch portfolios on mount and when username changes
	useEffect(() => {
		async function loadPortfolios() {
			if (!fallbackUsername) {
				setLoading(false)
				return
			}

			setLoading(true)
			setPortfolioError('')
			try {
				// Ensure user exists in backend (auto-create from Cognito profile if needed)
				const ensuredUser = await ensureCurrentUser()
				const resolvedUsername = ensuredUser?.username || fallbackUsername
				setAccountUsername(resolvedUsername)
				
				// Now fetch portfolios
				const data = await getPortfoliosByUser(resolvedUsername)
				setPortfolios(Array.isArray(data) ? data : [])
			} catch (err) {
				const message = err instanceof Error ? err.message : 'Failed to load portfolios'
				console.error('Portfolio fetch error:', { username: fallbackUsername, error: message })
				
				// Check if error is "User not found" - this means we need to create the user first
				if (message.includes('not found') || message.includes('User')) {
					setPortfolioError(
						`User account "${fallbackUsername}" not found in database. ` +
						'Please ensure your account is set up. If this is your first login, contact support.'
					)
				} else {
					setPortfolioError(message)
				}
				
				setPortfolios([])
			} finally {
				setLoading(false)
			}
		}

		loadPortfolios()
	}, [fallbackUsername])

	async function handleLogout() {
		setError('')

		try {
			await logout()
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Logout failed.')
		}
	}

	function handlePortfolioCreated(newPortfolio) {
		// Append new portfolio to list or refresh based on response
		if (newPortfolio && newPortfolio.portfolio_id) {
			// Backend returns {message, portfolio_id}. Fetch fresh data to get full portfolio object.
			const freshPortfolio = {
				id: newPortfolio.portfolio_id,
				name: '',
				description: '',
			}
			setPortfolios(prev => [...prev, freshPortfolio])
			// Optionally refresh the list to get the new portfolio data
			if (accountUsername) {
				getPortfoliosByUser(accountUsername)
					.then(data => {
						setPortfolios(Array.isArray(data) ? data : [])
					})
					.catch(() => {
						// Keep the optimistic update even if refresh fails
					})
			}
		}
	}

	function handlePortfolioDeleted(portfolioId) {
		setPortfolios(prev => prev.filter(p => p.id !== portfolioId))
		setPortfolioError('')
	}

	function handlePortfolioDeleteError(errorMessage) {
		setPortfolioError(errorMessage)
	}

	return (
		<main className="container py-4">
			<AppNavbar />

			<section className="mb-4">
				<h1 className="display-6 mb-2">Dashboard</h1>
				<p className="text-muted mb-0">
					You are signed in{user?.profile?.email ? ` as ${user.profile.email}` : ''}.
					{accountUsername && <span className="ms-3 badge bg-info">Username: {accountUsername}</span>}
				</p>
			</section>

			{error && (
				<div className="alert alert-danger" role="alert">
					{error}
				</div>
			)}

			<div className="row g-4">
				<div className="col-12 col-lg-6">
					<div className="card h-100 shadow-sm">
						<div className="card-header d-flex justify-content-between align-items-center">
							<h2 className="h4 mb-0">Portfolios</h2>
							<button
								className="btn btn-sm btn-primary"
								onClick={() => setIsModalOpen(true)}
								disabled={loading || !accountUsername}
							>
								+ New Portfolio
							</button>
						</div>
						<div className="card-body">
							<PortfolioList
								portfolios={portfolios}
								loading={loading}
								error={portfolioError}
								onDelete={handlePortfolioDeleted}
								onDeleteError={handlePortfolioDeleteError}
							/>
						</div>
					</div>
					<CreatePortfolioModal
						isOpen={isModalOpen}
						onClose={() => setIsModalOpen(false)}
						onPortfolioCreated={handlePortfolioCreated}
						username={accountUsername}
					/>
				</div>

				<div className="col-12 col-lg-6">
					<div className="card h-100 shadow-sm">
						<div className="card-body">
							<h2 className="h4 card-title">Holdings</h2>
							<p className="card-text text-muted">Current positions and market value snapshots will appear here.</p>
							<div className="border rounded-3 p-3 bg-light text-muted">Placeholder for holdings table or cards.</div>
						</div>
					</div>
				</div>

				<div className="col-12 col-lg-6">
					<div className="card h-100 shadow-sm">
						<div className="card-body">
							<h2 className="h4 card-title">Trade</h2>
							<p className="card-text text-muted">Buy and sell actions will be wired into this section.</p>
							<div className="border rounded-3 p-3 bg-light text-muted">Placeholder for trade form and order entry.</div>
						</div>
					</div>
				</div>

				<div className="col-12 col-lg-6">
					<div className="card h-100 shadow-sm">
						<div className="card-body">
							<h2 className="h4 card-title">Transactions</h2>
							<p className="card-text text-muted">Recent activity and trade history will appear here.</p>
							<div className="border rounded-3 p-3 bg-light text-muted">Placeholder for transaction timeline or table.</div>
						</div>
					</div>
				</div>
			</div>
		</main>
	)
}

export default DashboardPage