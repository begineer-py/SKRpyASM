import { NavLink, useNavigate } from 'react-router-dom';

function Navbar() {
  const navigate = useNavigate();

  const linkClass = ({ isActive }: { isActive: boolean }) => `c2-navbar__link${isActive ? ' active' : ''}`;

  return (
    <nav className="c2-navbar">
      <button
        className="c2-navbar__logo"
        onClick={() => navigate('/')}
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
      >
        <span className="c2-navbar__mark">ASM</span>
        SKRpyASM
      </button>

      <div className="c2-navbar__links">
        <NavLink to="/" end className={linkClass}>
          Targets
        </NavLink>
        <NavLink to="/execution-monitor" className={linkClass}>
          Monitor
        </NavLink>
        <NavLink to="/scheduler" className={linkClass}>
          Scheduler
        </NavLink>
        <span className="c2-navbar__divider" aria-hidden="true" />
        <NavLink to="/cve-intelligence" className={linkClass}>
          CVE Intel
        </NavLink>
        <NavLink to="/aicenter" className={linkClass}>
          AI Workbench
        </NavLink>
        <NavLink to="/skills" className={linkClass}>
          Skills
        </NavLink>
        <span className="c2-navbar__divider" aria-hidden="true" />
        <NavLink to="/agent-config" className={linkClass}>
          Agents
        </NavLink>
        <NavLink to="/api-keys" className={linkClass}>
          Keys
        </NavLink>
        <NavLink to="/pentest-config" className={linkClass}>
          Request Policy
        </NavLink>
      </div>

      <div className="c2-navbar__status" aria-label="System status online">
        <span className="c2-pulse" />
        Online
      </div>
    </nav>
  );
}

export default Navbar;
