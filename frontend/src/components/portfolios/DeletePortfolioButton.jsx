import { useState } from 'react'
import { deletePortfolio } from '../../services/api'

function DeletePortfolioButton({ portfolioId, portfolioName, onDelete, onDeleteError }) {
	const [isDeleting, setIsDeleting] = useState(false)

	async function handleDelete() {
		if (!confirm(`Are you sure you want to delete "${portfolioName}"?`)) {
			return
		}

		setIsDeleting(true)
		try {
			await deletePortfolio(portfolioId)
			onDelete(portfolioId)
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Failed to delete portfolio'
			onDeleteError(errorMessage)
		} finally {
			setIsDeleting(false)
		}
	}

	return (
		<button
			className="btn btn-sm btn-outline-danger"
			onClick={handleDelete}
			disabled={isDeleting}
		>
			{isDeleting ? 'Deleting...' : 'Delete'}
		</button>
	)
}

export default DeletePortfolioButton
