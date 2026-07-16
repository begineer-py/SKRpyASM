import { useState, type PropsWithChildren } from "react";

import Navbar from "../../components/Navbar";

const NAV_COLLAPSED_STORAGE_KEY = "c2_nav_collapsed";

function readNavCollapsedPreference(): boolean {
  try {
    const storedValue = localStorage.getItem(NAV_COLLAPSED_STORAGE_KEY);

    if (storedValue === "true") return true;
    if (storedValue === "false") return false;

    return true;
  } catch {
    return true;
  }
}

function persistNavCollapsedPreference(collapsed: boolean): void {
  try {
    localStorage.setItem(NAV_COLLAPSED_STORAGE_KEY, String(collapsed));
  } catch {
    return undefined;
  }
}

export default function MainLayout({ children }: PropsWithChildren) {
  const [navCollapsed, setNavCollapsed] = useState(readNavCollapsedPreference);

  const toggleNav = () => {
    setNavCollapsed((value) => {
      const next = !value;
      persistNavCollapsedPreference(next);
      return next;
    });
  };

  return (
    <div className={`c2-app-shell${navCollapsed ? " is-nav-collapsed" : " is-nav-expanded"}`}>
      <Navbar collapsed={navCollapsed} onToggleCollapse={toggleNav} />
      <main className="c2-app-shell__main">{children}</main>
    </div>
  );
}
