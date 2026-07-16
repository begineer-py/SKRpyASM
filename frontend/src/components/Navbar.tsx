import { useEffect, useState, type ComponentType } from 'react';
import { Activity, Bot, BriefcaseBusiness, KeyRound, Menu, PanelLeftClose, PanelLeftOpen, Radar, ScanSearch, Settings2, ShieldAlert, Timer } from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';

import { Drawer, DrawerContent, DrawerDescription, DrawerDismiss, DrawerHeader, DrawerTitle, DrawerTrigger } from './ui/drawer';

interface NavbarProps {
  readonly collapsed: boolean;
  readonly onToggleCollapse: () => void;
}

interface NavigationItem {
  readonly label: string;
  readonly path: string;
  readonly icon: ComponentType<{ readonly size?: number; readonly strokeWidth?: number; readonly 'aria-hidden'?: boolean }>;
  readonly end?: boolean;
}

interface NavigationGroup {
  readonly label: string;
  readonly items: readonly NavigationItem[];
}

const navigationGroups = [
  {
    label: '作業',
    items: [
      { label: '目標', path: '/', icon: Radar, end: true },
      { label: '執行監控', path: '/execution-monitor', icon: Activity },
      { label: '排程', path: '/scheduler', icon: Timer },
    ],
  },
  {
    label: '分析',
    items: [
      { label: '漏洞', path: '/vulnerabilities', icon: ShieldAlert },
      { label: 'CVE 情報', path: '/cve-intelligence', icon: ScanSearch },
      { label: 'AI 工作台', path: '/aicenter', icon: Bot },
      { label: '技能庫', path: '/skills', icon: BriefcaseBusiness },
    ],
  },
] satisfies readonly NavigationGroup[];

const settingsNavigation = [
  { label: 'Agent 設定', path: '/agent-config', icon: Settings2 },
  { label: 'API 金鑰', path: '/api-keys', icon: KeyRound },
  { label: '請求政策', path: '/pentest-config', icon: Settings2 },
] satisfies readonly NavigationItem[];

const settingsPaths = settingsNavigation.map(({ path }) => path);

function NavigationLink({ item, onNavigate }: { readonly item: NavigationItem; readonly onNavigate?: () => void }) {
  const Icon = item.icon;
  const location = useLocation();
  const isActive = item.end
    ? location.pathname === item.path
    : location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);

  return (
    <NavLink
      to={item.path}
      end={item.end}
      className={`c2-navbar__link${isActive ? ' active' : ''}`}
      aria-label={item.label}
      aria-current={isActive ? 'page' : undefined}
      data-tooltip={item.label}
      title={item.label}
      onClick={onNavigate}
    >
      <Icon size={18} strokeWidth={1.8} aria-hidden />
      <span className="c2-navbar__link-label">{item.label}</span>
    </NavLink>
  );
}

function NavigationGroups({ onNavigate, includeSettings = false }: { readonly onNavigate?: () => void; readonly includeSettings?: boolean }) {
  return (
    <>
      {navigationGroups.map((group) => (
        <section className="c2-navbar__group" key={group.label} aria-label={group.label}>
          <p className="c2-navbar__group-label">{group.label}</p>
          {group.items.map((item) => <NavigationLink item={item} key={item.path} onNavigate={onNavigate} />)}
        </section>
      ))}
      {includeSettings && (
        <section className="c2-navbar__group" aria-label="系統">
          <p className="c2-navbar__group-label">系統</p>
          {settingsNavigation.map((item) => <NavigationLink item={item} key={item.path} onNavigate={onNavigate} />)}
        </section>
      )}
    </>
  );
}

function Navbar({ collapsed, onToggleCollapse }: NavbarProps) {
  const location = useLocation();
  const [isMobileNavigationOpen, setIsMobileNavigationOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(() => settingsPaths.includes(location.pathname));

  useEffect(() => {
    if (settingsPaths.includes(location.pathname)) setIsSettingsOpen(true);
  }, [location.pathname]);

  return (
    <>
      <nav className={`c2-navbar${collapsed ? ' is-collapsed' : ''}`} aria-label="主要導覽">
      <div className="c2-navbar__topline">
        <div className="c2-navbar__logo" aria-label="SKRpyASM">
          <span className="c2-navbar__mark" aria-hidden>ASM</span>
          <span className="c2-navbar__brand-copy"><strong>SKRpyASM</strong><small>surface intelligence</small></span>
        </div>
        <button
          className="c2-navbar__collapse-toggle"
          type="button"
          onClick={onToggleCollapse}
          aria-label={collapsed ? '展開導覽列' : '收合導覽列'}
          title={collapsed ? '展開導覽列' : '收合導覽列'}
        >
          {collapsed ? <PanelLeftOpen size={18} aria-hidden /> : <PanelLeftClose size={18} aria-hidden />}
        </button>
      </div>

      <div className="c2-navbar__links">
        <NavigationGroups />
      </div>

      <div className="c2-navbar__settings">
        <button
          className={`c2-navbar__settings-trigger${isSettingsOpen ? ' active' : ''}`}
          type="button"
          onClick={() => setIsSettingsOpen((value) => !value)}
          aria-expanded={isSettingsOpen}
          aria-controls="c2-system-navigation"
          aria-label="系統設定"
          data-tooltip="系統設定"
          title="系統設定"
        >
          <Settings2 size={18} strokeWidth={1.8} aria-hidden />
          <span className="c2-navbar__link-label">系統設定</span>
        </button>
        {isSettingsOpen && (
          <div className="c2-navbar__settings-panel" id="c2-system-navigation">
            {settingsNavigation.map((item) => <NavigationLink item={item} key={item.path} />)}
          </div>
        )}
      </div>
      </nav>

      <Drawer open={isMobileNavigationOpen} onOpenChange={setIsMobileNavigationOpen}>
        <header className="c2-mobile-nav">
          <div className="c2-mobile-nav__brand" aria-label="SKRpyASM">
            <span className="c2-navbar__mark" aria-hidden>ASM</span>
            <strong>SKRpyASM</strong>
          </div>
          <DrawerTrigger className="c2-mobile-nav__trigger" aria-label="開啟導覽列" title="開啟導覽列">
            <Menu size={20} aria-hidden />
          </DrawerTrigger>
        </header>
        <DrawerContent className="c2-mobile-nav-drawer">
          <DrawerHeader>
            <div>
              <DrawerTitle>導覽</DrawerTitle>
              <DrawerDescription>選擇工作區或系統設定。</DrawerDescription>
            </div>
            <DrawerDismiss />
          </DrawerHeader>
          <nav className="c2-mobile-nav-drawer__links" aria-label="主要導覽">
            <NavigationGroups includeSettings onNavigate={() => setIsMobileNavigationOpen(false)} />
          </nav>
        </DrawerContent>
      </Drawer>
    </>
  );
}

export default Navbar;
