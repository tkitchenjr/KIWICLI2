import { useEffect, useState } from 'react'
import HoldingsPanel from '../components/holdings/HoldingsPanel'
import AppNavbar from '../components/layout/AppNavbar'
import CreatePortfolioModal from '../components/portfolios/CreatePortfolioModal'
import PortfolioList from '../components/portfolios/PortfolioList'
import { useAuth } from '../context/AuthContext'
import {
	ensureCurrentUser,
	getPortfolioById,
	getPortfolioTransactions,
	getPortfoliosByUser,
} from '../services/api'

function DashboardPage() {
	const { user, logout } = useAuth()
	const [error, setError] = useState('')
	const [portfolios, setPortfolios] = useState([])
	const [loading, setLoading] = useState(true)
	const [portfolioError, setPortfolioError] = useState('')
	const [isModalOpen, setIsModalOpen] = useState(false)
	const [accountUsername, setAccountUsername] = useState('')
	const [selectedPortfolioId, setSelectedPortfolioId] = useState(null)
	const [selectedPortfolio, setSelectedPortfolio] = useState(null)
	const [holdings, setHoldings] = useState([])
	const [holdingsLoading, setHoldingsLoading] = useState(false)
	const [holdingsError, setHoldingsError] = useState('')
	const [transactions, setTransactions] = useState([])
	const [transactionsLoading, setTransactionsLoading] = useState(false)
	const [transactionsError, setTransactionsError] = useState('')

	const fallbackUsername =
		user?.profile?.preferred_username ||
		user?.profile?.['cognito:username'] ||
		user?.profile?.email ||
		''

	useEffect(() => {
		async function loadPortfolios() {
			if (!fallbackUsername) {
				setLoading(false)
				return
			}

			setLoading(true)
			setPortfolioError('')

			try {
				let resolvedUsername = fallbackUsername
				try {
					const ensuredUser = await ensureCurrentUser()
					resolvedUsername = ensuredUser?.username || fallbackUsername
				} catch (ensureError) {
					const ensureMessage =
						ensureError instanceof Error ? ensureError.message : 'User ensure failed'
					console.warn('ensureCurrentUser failed; continuing with fallback username', {
						fallbackUsername,
						error: ensureMessage,
					})
				}

				setAccountUsername(resolvedUsername)

				const data = await getPortfoliosByUser(resolvedUsername)
				const normalizedPortfolios = Array.isArray(data) ? data : []
				setPortfolios(normalizedPortfolios)

				setSelectedPortfolioId((previousId) => {
					if (!normalizedPortfolios.length) {
						return null
					}

					const stillExists = normalizedPortfolios.some((portfolio) => portfolio.id === previousId)
					if (stillExists) {
						return previousId
					}

					return normalizedPortfolios[0].id
				})
			} catch (err) {
				const message = err instanceof Error ? err.message : 'Failed to load portfolios'
				setPortfolioError(message)
				setPortfolios([])
				setSelectedPortfolioId(null)
			} finally {
				setLoading(false)
			}
		}

		loadPortfolios()
	}, [fallbackUsername])

	useEffect(() => {
		async function loadPortfolioDetails() {
			if (!selectedPortfolioId) {
				setSelectedPortfolio(null)
				setHoldings([])
				setTransactions([])
				setHoldingsError('')
				setTransactionsError('')
				return
			}

			setHoldingsLoading(true)
			setTransactionsLoading(true)
			setHoldingsError('')
			setTransactionsError('')

			try {
				const [portfolioDetails, portfolioTransactions] = await Promise.all([
					getPortfolioById(selectedPortfolioId),
					getPortfolioTransactions(selectedPortfolioId),
				])

				setSelectedPortfolio(portfolioDetails || null)
				setHoldings(Array.isArray(portfolioDetails?.investments) ? portfolioDetails.investments : [])
				setTransactions(Array.isArray(portfolioTransactions) ? portfolioTransactions : [])
			} catch (err) {
				const message = err instanceof Error ? err.message : 'Failed to load selected portfolio details'
				setHoldingsError(message)
				setTransactionsError(message)
				setHoldings([])
				setTransactions([])
			} finally {
				setHoldingsLoading(false)
				setTransactionsLoading(false)
			}
		}

		loadPortfolioDetails()
	}, [selectedPortfolioId])

	async function refreshSelectedPortfolioData() {
		if (!selectedPortfolioId) {
			return
		}

		setHoldingsLoading(true)
		setTransactionsLoading(true)
		setHoldingsError('')
		setTransactionsError('')

		try {
			const [portfolioDetails, portfolioTransactions] = await Promise.all([
				getPortfolioById(selectedPortfolioId),
				getPortfolioTransactions(selectedPortfolioId),
			])
			setSelectedPortfolio(portfolioDetails || null)
			setHoldings(Array.isArray(portfolioDetails?.investments) ? portfolioDetails.investments : [])
			setTransactions(Array.isArray(portfolioTransactions) ? portfolioTransactions : [])
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to refresh portfolio data'
			setHoldingsError(message)
			setTransactionsError(message)
		} finally {
			setHoldingsLoading(false)
			setTransactionsLoading(false)
		}
	}

	async function handleLogout() {
		setError('')

		try {
			await logout()
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Logout failed.')
		}
	}

	function handlePortfolioCreated(newPortfolio) {
		if (!newPortfolio?.portfolio_id || !accountUsername) {
			return
		}

		setPortfolioError('')
		getPortfoliosByUser(accountUsername)
			.then((data) => {
				const normalizedPortfolios = Array.isArray(data) ? data : []
				setPortfolios(normalizedPortfolios)
				setSelectedPortfolioId(newPortfolio.portfolio_id)
			})
			.catch((err) => {
				setPortfolioError(err instanceof Error ? err.message : 'Failed to refresh portfolios')
			})
	}

	function handleSelectPortfolio(portfolio) {
		setSelectedPortfolioId(portfolio.id)
	}

	function handlePortfolioDeleted(portfolioId) {
		const remaining = portfolios.filter((portfolio) => portfolio.id !== portfolioId)
		setPortfolios(remaining)
		setPortfolioError('')

		if (selectedPortfolioId === portfolioId) {
			setSelectedPortfolioId(remaining.length ? remaining[0].id : null)
		}
	}

	function handlePortfolioDeleteError(errorMessage) {
		setPortfolioError(errorMessage)
	}

	return (
		<main className="container py-4">
			<AppNavbar />

			<section className="mb-4 d-flex justify-content-between align-items-end">
				<div>
					<h1 className="display-6 mb-2">Dashboard</h1>
					<p className="text-muted mb-0">
						You are signed in{user?.profile?.email ? ` as ${user.profile.email}` : ''}.
						{accountUsername && <span className="ms-3 badge bg-info">Username: {accountUsername}</span>}
					</p>
				</div>
				<button className="btn btn-outline-secondary btn-sm" onClick={handleLogout}>Sign out</button>
			</section>

			{error && (
				<div className="alert alert-danger" role="alert">
					{error}
				</div>
			)}

			<div className="row g-4">
				<div className="col-12 col-xl-5">
					<div className="card shadow-sm">
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
								selectedPortfolioId={selectedPortfolioId}
								onSelect={handleSelectPortfolio}
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

				<div className="col-12 col-xl-7">
					<HoldingsPanel
						selectedPortfolio={selectedPortfolio}
						holdings={holdings}
						holdingsLoading={holdingsLoading}
						holdingsError={holdingsError}
						onTradeSuccess={refreshSelectedPortfolioData}
					/>
				</div>

				<div className="col-12">
					<div className="card shadow-sm">
						<div className="card-body">
							<h2 className="h4 card-title">Transactions</h2>
							<p className="card-text text-muted">
								{selectedPortfolio
									? `Recent activity for ${selectedPortfolio.name}`
									: 'Select a portfolio to view transaction history.'}
							</p>

							{transactionsError && (
								<div className="alert alert-danger py-2" role="alert">
									{transactionsError}
								</div>
							)}

							{transactionsLoading ? (
								<div className="text-center py-3">
									<div className="spinner-border" role="status">
										<span className="visually-hidden">Loading transactions...</span>
									</div>
								</div>
							) : transactions.length === 0 ? (
								<div className="alert alert-info mb-0" role="alert">
									No transactions for this portfolio yet.
								</div>
							) : (
								<div className="table-responsive">
									<table className="table table-sm align-middle mb-0">
										<thead>
											<tr>
												<th scope="col">Date</th>
												<th scope="col">Type</th>
												<th scope="col">Ticker</th>
												<th scope="col">Qty</th>
												<th scope="col">Price</th>
											</tr>
										</thead>
										<tbody>
											{transactions.map((transaction) => (
												<tr key={transaction.transaction_id}>
													<td>{new Date(transaction.date_time).toLocaleString()}</td>
													<td>
														<span className={`badge ${transaction.transaction_type === 'BUY' ? 'text-bg-success' : 'text-bg-danger'}`}>
															{transaction.transaction_type}
														</span>
													</td>
													<td>{transaction.ticker}</td>
													<td>{transaction.quantity}</td>
													<td>${Number(transaction.price).toFixed(2)}</td>
												</tr>
											))}
										</tbody>
									</table>
								</div>
							)}
						</div>
					</div>
				</div>
			</div>
		</main>
	)
}

export default DashboardPage
