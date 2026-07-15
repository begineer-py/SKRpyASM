import { useState, type PropsWithChildren } from "react";

import Navbar from "../../components/Navbar";

export default function MainLayout({ children }: PropsWithChildren) {
  const [navCollapsed, setNavCollapsed] = useState(() => {
    try {
      return localStorage.getItem('c2_nav_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  const toggleNav = () => {
    setNavCollapsed((value) => {
      const next = !value;
      localStorage.setItem('c2_nav_collapsed', String(next));
      return next;
    });
  };

  return (
    <div className={`c2-app-shell${navCollapsed ? " is-nav-collapsed" : ""}`}>
      <Navbar collapsed={navCollapsed} onToggleCollapse={toggleNav} />
      <main className="c2-app-shell__main">{children}</main>
    </div>
  );
}
