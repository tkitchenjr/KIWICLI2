import { useState } from 'react'
import { createPortfolio } from '../../services/api'

function CreatePortfolioModal({ isOpen, onClose, onPortfolioCreated, username }) {
	const [formData, setFormData] = useState({ name: '', description: '' })
	const [isSubmitting, setIsSubmitting] = useState(false)
	const [error, setError] = useState('')

	function handleInputChange(e) {
		const { name, value } = e.target
		setFormData(prev => ({
			...prev,
			[name]: value,
		}))
	}

	async function handleSubmit(e) {
		e.preventDefault()
		setError('')

		if (!formData.name.trim()) {
			setError('Portfolio name is required')
			return
		}

		if (!formData.description.trim()) {
			setError('Portfolio description is required')
			return
		}

		setIsSubmitting(true)
		try {
			const response = await createPortfolio(
				formData.name.trim(),
				formData.description.trim(),
				username,
			)
			onPortfolioCreated(response)
			setFormData({ name: '', description: '' })
			onClose()
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to create portfolio'
			setError(message)
		} finally {
			setIsSubmitting(false)
		}
	}

	if (!isOpen) return null

	return (
		<div
			className="modal show d-block"
			tabIndex="-1"
			style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
		>
			<div className="modal-dialog">
				<div className="modal-content">
					<div className="modal-header">
						<h5 className="modal-title">Create Portfolio</h5>
						<button
							type="button"
							className="btn-close"
							onClick={onClose}
							disabled={isSubmitting}
						/>
					</div>
					<form onSubmit={handleSubmit}>
						<div className="modal-body">
							{error && (
								<div className="alert alert-danger mb-3" role="alert">
									{error}
								</div>
							)}
							<div className="mb-3">
								<label htmlFor="portfolioName" className="form-label">
									Portfolio Name
								</label>
								<input
									type="text"
									className="form-control"
									id="portfolioName"
									name="name"
									value={formData.name}
									onChange={handleInputChange}
									placeholder="e.g., My Investment Portfolio"
									disabled={isSubmitting}
									required
								/>
							</div>
							<div className="mb-3">
								<label htmlFor="portfolioDescription" className="form-label">
									Description
								</label>
								<textarea
									className="form-control"
									id="portfolioDescription"
									name="description"
									value={formData.description}
									onChange={handleInputChange}
									placeholder="Describe the purpose of this portfolio"
									rows="3"
									disabled={isSubmitting}
									required
								/>
							</div>
						</div>
						<div className="modal-footer">
							<button
								type="button"
								className="btn btn-secondary"
								onClick={onClose}
								disabled={isSubmitting}
							>
								Cancel
							</button>
							<button
								type="submit"
								className="btn btn-primary"
								disabled={isSubmitting}
							>
								{isSubmitting ? 'Creating...' : 'Create Portfolio'}
							</button>
						</div>
					</form>
				</div>
			</div>
		</div>
	)
}

export default CreatePortfolioModal
