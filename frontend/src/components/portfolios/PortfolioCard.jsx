import DeletePortfolioButton from './DeletePortfolioButton'

function PortfolioCard({ portfolio, isSelected, onSelect, onDelete, onDeleteError }) {
	return (
		<div
			role="button"
			tabIndex={0}
			className={`card shadow-sm mb-3 w-100 text-start border ${isSelected ? 'border-primary' : 'border-light'}`}
			onClick={() => onSelect(portfolio)}
			onKeyDown={(event) => {
				if (event.key === 'Enter' || event.key === ' ') {
					event.preventDefault()
					onSelect(portfolio)
				}
			}}
			style={{ backgroundColor: isSelected ? '#e7f1ff' : 'white' }}
		>
			<div className="card-body">
				<div className="d-flex justify-content-between align-items-start">
					<div className="flex-grow-1">
						<h5 className="card-title d-flex align-items-center gap-2">
							<span>{portfolio.name}</span>
							{isSelected && <span className="badge text-bg-primary">Selected</span>}
						</h5>
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
