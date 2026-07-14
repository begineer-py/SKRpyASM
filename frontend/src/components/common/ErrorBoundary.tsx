import { Component, type ErrorInfo, type PropsWithChildren, type ReactNode } from "react";

interface ErrorBoundaryState {
  error: Error | null;
}

export default class ErrorBoundary extends Component<
  PropsWithChildren,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Unhandled application error", error, errorInfo);
  }

  render(): ReactNode {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <section className="c2-page" role="alert">
        <div className="c2-card mx-auto max-w-2xl p-6">
          <p className="mb-2 font-mono text-xs uppercase tracking-[0.16em] text-red">
            Application error
          </p>
          <h1 className="mb-3 text-xl font-semibold text-text-primary">
            This view could not be rendered.
          </h1>
          <p className="text-sm text-text-secondary">
            Refresh the page and try again. If the problem persists, check the
            browser console for the captured error.
          </p>
        </div>
      </section>
    );
  }
}
