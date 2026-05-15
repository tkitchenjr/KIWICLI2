import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function ProtectedRoute({ children }) {
	const { isAuthenticated, isLoading } = useAuth()
	const location = useLocation()

	if (isLoading) {
		return <main style={{ padding: '2rem' }}>Checking session...</main>
	}

	if (!isAuthenticated) {
		return <Navigate to="/" replace state={{ from: location }} />
	}

	return children
}

export default ProtectedRoute