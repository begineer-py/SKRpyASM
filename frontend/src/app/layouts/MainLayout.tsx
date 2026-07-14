import type { PropsWithChildren } from "react";

import Navbar from "../../components/Navbar";

export default function MainLayout({ children }: PropsWithChildren) {
  return (
    <>
      <Navbar />
      <main>{children}</main>
    </>
  );
}
