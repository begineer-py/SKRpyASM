import { NavLink, useNavigate } from 'react-router-dom';

function Navbar() {
  const navigate = useNavigate();

  return (
    <nav className="c2-navbar">
      {/* Logo */}
      <button
        className="c2-navbar__logo"
        onClick={() => navigate('/')}
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
      >
        &gt;_ C2 PLATFORM
      </button>

      {/* Nav Links */}
      <div className="c2-navbar__links">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `c2-navbar__link${isActive ? ' active' : ''}`}
        >
          Targets
        </NavLink>
        <NavLink
          to="/execution-monitor"
          className={({ isActive }) => `c2-navbar__link${isActive ? ' active' : ''}`}
        >
          Monitor
        </NavLink>
        <NavLink
          to="/aicenter"
          className={({ isActive }) => `c2-navbar__link${isActive ? ' active' : ''}`}
        >
          AI Center
        </NavLink>
        <NavLink
          to="/cve-intelligence"
          className={({ isActive }) => `c2-navbar__link${isActive ? ' active' : ''}`}
        >
          CVE Intel
        </NavLink>
        <NavLink
          to="/scheduler"
          className={({ isActive }) => `c2-navbar__link${isActive ? ' active' : ''}`}
        >
          Scheduler
        </NavLink>
        <NavLink
          to="/skills"
          className={({ isActive }) => `c2-navbar__link${isActive ? ' active' : ''}`}
        >
          Skills
        </NavLink>
        <NavLink
          to="/api-keys"
          className={({ isActive }) => `c2-navbar__link${isActive ? ' active' : ''}`}
        >
          Keys
        </NavLink>
      </div>

      {/* Status indicator */}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="c2-pulse" />
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          Online
        </span>
      </div>
    </nav>
  );
}

export default Navbar;
