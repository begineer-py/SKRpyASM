import type { PropsWithChildren } from "react";

import Navbar from "../../components/Navbar";

export default function MainLayout({ children }: PropsWithChildren) {
  return (
    <div className="c2-app-shell">
      <Navbar />
      <main className="c2-app-shell__main">{children}</main>
    </div>
  );
}
