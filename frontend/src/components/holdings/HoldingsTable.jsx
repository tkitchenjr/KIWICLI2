import HoldingRow from './HoldingRow'

function HoldingsTable({ holdings }) {
	if (!holdings || holdings.length === 0) {
		return (
			<div className="alert alert-info mb-0" role="alert">
				No holdings in this portfolio yet.
			</div>
		)
	}

	return (
		<div className="table-responsive">
			<table className="table table-sm align-middle mb-0">
				<thead>
					<tr>
						<th scope="col">Ticker</th>
						<th scope="col">Quantity</th>
					</tr>
				</thead>
				<tbody>
					{holdings.map((holding) => (
						<HoldingRow key={holding.ticker} holding={holding} />
					))}
				</tbody>
			</table>
		</div>
	)
}

export default HoldingsTable
