import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Flights' },
  { to: '/aircraft', label: 'Aircraft' },
  { to: '/airports', label: 'Airports' },
  { to: '/registrations', label: 'Registrations' },
]

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Flight diary</p>
          <h1>✈️ Flight Data</h1>
        </div>
        <nav className="app-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => (isActive ? 'nav-link nav-link-active' : 'nav-link')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="page-shell">{children}</main>
    </div>
  )
}
