import { useState } from 'react';
import { Activity, Bot, BriefcaseBusiness, ChevronRight, KeyRound, Menu, Radar, ScanSearch, Settings2, ShieldAlert, Timer, X } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';

function Navbar() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const linkClass = ({ isActive }: { isActive: boolean }) => `c2-navbar__link${isActive ? ' active' : ''}`;
  const closeMenu = () => setIsOpen(false);

  return (
    <nav className={`c2-navbar${isOpen ? ' is-open' : ''}`}>
      <div className="c2-navbar__topline">
      <button
        className="c2-navbar__logo bg-transparent border-none cursor-pointer p-0"
        onClick={() => { navigate('/'); closeMenu(); }}
      >
        <span className="c2-navbar__mark">ASM</span>
        <span className="c2-navbar__brand-copy"><strong>SKRpyASM</strong><small>surface intelligence</small></span>
      </button>
      <button className="c2-navbar__menu-toggle" type="button" aria-label={isOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={isOpen} onClick={() => setIsOpen((value) => !value)}>
        {isOpen ? <X size={18} /> : <Menu size={18} />}
      </button>
      </div>

      <div className="c2-navbar__links" onClick={closeMenu}>
        <div className="c2-navbar__group-label"><span>01</span> OPERATIONS</div>
        <NavLink to="/" end className={linkClass}><Radar size={16} strokeWidth={1.8} />
          Targets
        </NavLink>
        <NavLink to="/execution-monitor" className={linkClass}><Activity size={16} strokeWidth={1.8} />
          Monitor
        </NavLink>
        <NavLink to="/scheduler" className={linkClass}><Timer size={16} strokeWidth={1.8} />
          Scheduler
        </NavLink>
        <div className="c2-navbar__group-label"><span>02</span> ANALYSIS</div>
        <NavLink to="/vulnerabilities" className={linkClass}><ShieldAlert size={16} strokeWidth={1.8} />
          Vulns
        </NavLink>
        <NavLink to="/cve-intelligence" className={linkClass}><ScanSearch size={16} strokeWidth={1.8} />
          CVE Intel
        </NavLink>
        <NavLink to="/aicenter" className={linkClass}><Bot size={16} strokeWidth={1.8} />
          AI Workbench
        </NavLink>
        <NavLink to="/skills" className={linkClass}><BriefcaseBusiness size={16} strokeWidth={1.8} />
          Skills
        </NavLink>
        <div className="c2-navbar__group-label"><span>03</span> SYSTEM</div>
        <NavLink to="/agent-config" className={linkClass}><Settings2 size={16} strokeWidth={1.8} />
          Agents
        </NavLink>
        <NavLink to="/api-keys" className={linkClass}><KeyRound size={16} strokeWidth={1.8} />
          Keys
        </NavLink>
        <NavLink to="/pentest-config" className={linkClass}><Settings2 size={16} strokeWidth={1.8} />
          Request Policy
        </NavLink>
      </div>

      <div className="c2-navbar__status" aria-label="System status online">
        <span className="c2-pulse" />
        <span><strong>Operational</strong><small>All systems nominal</small></span>
        <ChevronRight size={14} />
      </div>
    </nav>
  );
}

export default Navbar;
