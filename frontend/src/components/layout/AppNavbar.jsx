import { useAuth } from '../../context/AuthContext'

function AppNavbar() {
	const { user, logout } = useAuth()

	const displayName =
		user?.profile?.email ||
		user?.profile?.name ||
		user?.profile?.preferred_username ||
		'Authenticated user'

	return (
		<nav className="navbar navbar-expand-lg navbar-dark bg-dark px-3 py-3 rounded-3 shadow-sm mb-4">
			<div className="container-fluid p-0">
				<div className="d-flex flex-column flex-md-row align-items-md-center gap-2">
					<span className="navbar-brand mb-0 h1">KIWI CLI</span>
					<span className="badge text-bg-secondary align-self-start align-self-md-center">
						{displayName}
					</span>
				</div>

				<button type="button" className="btn btn-outline-light" onClick={logout}>
					Logout
				</button>
			</div>
		</nav>
	)
}

export default AppNavbar
