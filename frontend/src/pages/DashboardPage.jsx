import { useState } from 'react'
import AppNavbar from '../components/layout/AppNavbar'
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
		<main className="container py-4">
			<AppNavbar />

			<section className="mb-4">
				<h1 className="display-6 mb-2">Dashboard</h1>
				<p className="text-muted mb-0">
					You are signed in{user?.profile?.email ? ` as ${user.profile.email}` : ''}.
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
						<div className="card-body">
							<h2 className="h4 card-title">Portfolios</h2>
							<p className="card-text text-muted">Portfolio summary and account overview will appear here.</p>
							<div className="border rounded-3 p-3 bg-light text-muted">Placeholder for portfolio list and controls.</div>
						</div>
					</div>
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