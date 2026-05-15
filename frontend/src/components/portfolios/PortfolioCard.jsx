import DeletePortfolioButton from './DeletePortfolioButton'

function PortfolioCard({ portfolio, onDelete, onDeleteError }) {
	return (
		<div className="card shadow-sm mb-3">
			<div className="card-body">
				<div className="d-flex justify-content-between align-items-start">
					<div className="flex-grow-1">
						<h5 className="card-title">{portfolio.name}</h5>
						{portfolio.description && (
							<p className="card-text text-muted small">{portfolio.description}</p>
						)}
						<small className="text-secondary">ID: {portfolio.id}</small>
					</div>
					<DeletePortfolioButton
						portfolioId={portfolio.id}
						portfolioName={portfolio.name}
						onDelete={onDelete}
						onDeleteError={onDeleteError}
					/>
				</div>
			</div>
		</div>
	)
}

export default PortfolioCard
