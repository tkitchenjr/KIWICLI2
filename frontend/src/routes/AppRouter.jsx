import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AuthCallbackPage from '../pages/AuthCallbackPage'
import DashboardPage from '../pages/DashboardPage'
import LoginPage from '../pages/LoginPage'
import ProtectedRoute from './ProtectedRoute'

function AppRouter() {
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/" element={<LoginPage />} />
				<Route path="/login" element={<Navigate to="/" replace />} />
				<Route path="/callback" element={<AuthCallbackPage />} />
				<Route
					path="/dashboard"
					element={
						<ProtectedRoute>
							<DashboardPage />
						</ProtectedRoute>
					}
				/>
				<Route path="*" element={<Navigate to="/" replace />} />
			</Routes>
		</BrowserRouter>
	)
}

export default AppRouter
