import type { PropsWithChildren } from "react";

/**
 * Application-wide providers belong here so the entry point stays deliberately
 * small and feature pages do not need to know the provider composition.
 */
export default function Providers({ children }: PropsWithChildren) {
  return children;
}
