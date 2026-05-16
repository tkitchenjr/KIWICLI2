import HoldingsTable from './HoldingsTable'
import TradeForm from './TradeForm'

function HoldingsPanel({
	selectedPortfolio,
	holdings,
	holdingsLoading,
	holdingsError,
	onTradeSuccess,
}) {
	return (
		<div className="card h-100 shadow-sm">
			<div className="card-body d-flex flex-column gap-3">
				<div>
					<h2 className="h4 card-title mb-1">Holdings</h2>
					<p className="card-text text-muted mb-0">
						{selectedPortfolio
							? `Portfolio: ${selectedPortfolio.name}`
							: 'Select a portfolio to view holdings.'}
					</p>
				</div>

				{holdingsError && (
					<div className="alert alert-danger py-2" role="alert">
						{holdingsError}
					</div>
				)}

				{holdingsLoading ? (
					<div className="text-center py-4">
						<div className="spinner-border" role="status">
							<span className="visually-hidden">Loading holdings...</span>
						</div>
					</div>
				) : (
					<HoldingsTable holdings={holdings} />
				)}

				<div className="border-top pt-3">
					<h3 className="h5 mb-2">Trade</h3>
					<TradeForm
						selectedPortfolioId={selectedPortfolio?.id}
						holdings={holdings}
						onTradeSuccess={onTradeSuccess}
					/>
				</div>
			</div>
		</div>
	)
}

export default HoldingsPanel
