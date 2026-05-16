import PortfolioCard from './PortfolioCard'

function PortfolioList({ portfolios, loading, error, selectedPortfolioId, onSelect, onDelete, onDeleteError }) {
	if (loading) {
		return (
			<div className="text-center py-4">
				<div className="spinner-border" role="status">
					<span className="visually-hidden">Loading portfolios...</span>
				</div>
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
			{error && (
				<div className="alert alert-danger mb-3" role="alert">
					<strong>Error:</strong> {error}
				</div>
			)}
			{portfolios.map(portfolio => (
				<PortfolioCard
					key={portfolio.id}
					portfolio={portfolio}
					isSelected={portfolio.id === selectedPortfolioId}
					onSelect={onSelect}
					onDelete={onDelete}
					onDeleteError={onDeleteError}
				/>
			))}
		</div>
	)
}

export default PortfolioList
