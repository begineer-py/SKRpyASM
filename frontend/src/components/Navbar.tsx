import { useState } from 'react';
import { Activity, Bot, BriefcaseBusiness, KeyRound, Menu, PanelLeftClose, PanelLeftOpen, Radar, ScanSearch, Settings2, ShieldAlert, Timer, X } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
//定義收起功能屬性
interface NavbarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

function Navbar({ collapsed, onToggleCollapse }: NavbarProps) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const linkClass = ({ isActive }: { isActive: boolean }) => `c2-navbar__link${isActive ? ' active' : ''}`;
  const closeMenu = () => setIsOpen(false);

  return (
    <nav className={`c2-navbar${isOpen ? ' is-open' : ''}${collapsed ? ' is-collapsed' : ''}`}>
      <div className="c2-navbar__topline">
      <button
        className="c2-navbar__logo bg-transparent border-none cursor-pointer p-0"
        onClick={() => { navigate('/'); closeMenu(); }}
      >
        <span className="c2-navbar__mark">ASM</span>
        <span className="c2-navbar__brand-copy"><strong>SKRpyASM</strong><small>surface intelligence</small></span>
      </button>
      <button
        className="c2-navbar__collapse-toggle"
        type="button"
        onClick={onToggleCollapse}
        aria-label={collapsed ? '展開導覽列' : '收合導覽列'}
        title={collapsed ? '展開導覽列' : '收合導覽列'}
      >
        {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
      </button>
      <button className="c2-navbar__menu-toggle" type="button" aria-label={isOpen ? '關閉導覽列' : '開啟導覽列'} aria-expanded={isOpen} onClick={() => setIsOpen((value) => !value)}>
        {isOpen ? <X size={18} /> : <Menu size={18} />}
      </button>
      </div>

      <div className="c2-navbar__links" onClick={closeMenu}>
        <div className="c2-navbar__group-label"><span>01</span> 作業</div>
        <NavLink to="/" end className={linkClass} title="目標"><Radar size={16} strokeWidth={1.8} />
          <span>目標</span>
        </NavLink>
        <NavLink to="/execution-monitor" className={linkClass} title="執行監控"><Activity size={16} strokeWidth={1.8} />
          <span>執行監控</span>
        </NavLink>
        <NavLink to="/scheduler" className={linkClass} title="排程"><Timer size={16} strokeWidth={1.8} />
          <span>排程</span>
        </NavLink>
        <div className="c2-navbar__group-label"><span>02</span> 分析</div>
        <NavLink to="/vulnerabilities" className={linkClass} title="漏洞"><ShieldAlert size={16} strokeWidth={1.8} />
          <span>漏洞</span>
        </NavLink>
        <NavLink to="/cve-intelligence" className={linkClass} title="CVE 情報"><ScanSearch size={16} strokeWidth={1.8} />
          <span>CVE 情報</span>
        </NavLink>
        <NavLink to="/aicenter" className={linkClass} title="AI 工作台"><Bot size={16} strokeWidth={1.8} />
          <span>AI 工作台</span>
        </NavLink>
        <NavLink to="/skills" className={linkClass} title="技能庫"><BriefcaseBusiness size={16} strokeWidth={1.8} />
          <span>技能庫</span>
        </NavLink>
        <div className="c2-navbar__group-label"><span>03</span> 系統</div>
        <NavLink to="/agent-config" className={linkClass} title="Agent 設定"><Settings2 size={16} strokeWidth={1.8} />
          <span>Agent 設定</span>
        </NavLink>
        <NavLink to="/api-keys" className={linkClass} title="API 金鑰"><KeyRound size={16} strokeWidth={1.8} />
          <span>API 金鑰</span>
        </NavLink>
        <NavLink to="/pentest-config" className={linkClass} title="請求政策"><Settings2 size={16} strokeWidth={1.8} />
          <span>請求政策</span>
        </NavLink>
      </div>
    </nav>
  );
}

export default Navbar;
