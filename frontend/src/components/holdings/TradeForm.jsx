import { useState } from 'react'
import { executeBuyOrder, executeSellOrder } from '../../services/api'

function TradeForm({ selectedPortfolioId, holdings = [], onTradeSuccess }) {
	const [ticker, setTicker] = useState('')
	const [quantity, setQuantity] = useState('')
	const [isLoading, setIsLoading] = useState(false)
	const [successMessage, setSuccessMessage] = useState('')
	const [errorMessage, setErrorMessage] = useState('')
	const normalizedTicker = ticker.trim().toUpperCase()
	const ownedQuantity = holdings.find((holding) => holding.ticker === normalizedTicker)?.quantity ?? 0

	function validateForm(type) {
		if (!selectedPortfolioId) {
			setErrorMessage('Select a portfolio before placing a trade.')
			return false
		}

		if (!normalizedTicker) {
			setErrorMessage('Ticker symbol is required.')
			return false
		}

		const parsedQuantity = Number(quantity)
		if (!Number.isInteger(parsedQuantity) || parsedQuantity <= 0) {
			setErrorMessage('Quantity must be a positive whole number.')
			return false
		}

		if (type === 'sell' && parsedQuantity > ownedQuantity) {
			setErrorMessage(`You only hold ${ownedQuantity} share(s) of ${normalizedTicker}.`)
			return false
		}

		return true
	}

	async function submitTrade(type) {
		setSuccessMessage('')
		setErrorMessage('')

		if (!validateForm(type)) {
			return
		}

		setIsLoading(true)
		const parsedQuantity = Number(quantity)

		try {
			if (type === 'buy') {
				await executeBuyOrder(selectedPortfolioId, normalizedTicker, parsedQuantity)
				setSuccessMessage(`Bought ${parsedQuantity} share(s) of ${normalizedTicker}.`)
			} else {
				await executeSellOrder(selectedPortfolioId, normalizedTicker, parsedQuantity)
				setSuccessMessage(`Sold ${parsedQuantity} share(s) of ${normalizedTicker}.`)
			}

			await onTradeSuccess()
			setQuantity('')
		} catch (error) {
			setErrorMessage(error instanceof Error ? error.message : 'Trade failed.')
		} finally {
			setIsLoading(false)
		}
	}

	return (
		<div>
			{successMessage && (
				<div className="alert alert-success py-2" role="alert">
					{successMessage}
				</div>
			)}

			{errorMessage && (
				<div className="alert alert-danger py-2" role="alert">
					{errorMessage}
				</div>
			)}

			<div className="row g-2 align-items-end">
				<div className="col-12 col-md-4">
					<label htmlFor="tradeTicker" className="form-label mb-1">Ticker</label>
					<input
						id="tradeTicker"
						type="text"
						className="form-control"
						value={ticker}
						onChange={(event) => setTicker(event.target.value)}
						placeholder="AAPL"
						disabled={isLoading}
					/>
				</div>
				<div className="col-12 col-md-4">
					<label htmlFor="tradeQuantity" className="form-label mb-1">Quantity</label>
					<input
						id="tradeQuantity"
						type="number"
						min="1"
						step="1"
						className="form-control"
						value={quantity}
						onChange={(event) => setQuantity(event.target.value)}
						disabled={isLoading}
					/>
				</div>
				<div className="col-12 col-md-4 d-flex gap-2">
					<button
						type="button"
						className="btn btn-success flex-grow-1"
						onClick={() => submitTrade('buy')}
						disabled={isLoading}
					>
						{isLoading ? 'Working...' : 'Buy'}
					</button>
					<button
						type="button"
						className="btn btn-danger flex-grow-1"
						onClick={() => submitTrade('sell')}
						disabled={isLoading}
					>
						{isLoading ? 'Working...' : 'Sell'}
					</button>
				</div>
			</div>
		</div>
	)
}

export default TradeForm
