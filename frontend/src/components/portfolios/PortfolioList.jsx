import PortfolioCard from './PortfolioCard'

function PortfolioList({ portfolios, loading, error, onDelete, onDeleteError }) {
	if (loading) {
		return (
			<div className="text-center py-4">
				<div className="spinner-border" role="status">
					<span className="visually-hidden">Loading portfolios...</span>
				</div>
			</div>
		)
	}

	if (error) {
		return (
			<div className="alert alert-danger" role="alert">
				<strong>Error:</strong> {error}
			</div>
		)
	}

	if (!portfolios || portfolios.length === 0) {
		return (
			<div className="alert alert-info" role="alert">
				<strong>No portfolios yet.</strong> Create your first portfolio to get started.
			</div>
		)
	}

	return (
		<div>
			{portfolios.map(portfolio => (
				<PortfolioCard
					key={portfolio.id}
					portfolio={portfolio}
					onDelete={onDelete}
					onDeleteError={onDeleteError}
				/>
			))}
		</div>
	)
}

export default PortfolioList
