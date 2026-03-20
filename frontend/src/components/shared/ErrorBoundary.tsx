/* Lightweight error boundary for map and chart rendering failures. */

import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  title: string;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = { hasError: false };

  public static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  public componentDidCatch(_error: Error, _info: ErrorInfo): void {}

  public render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="rounded-3xl border border-um-red/40 bg-um-red/10 p-6 text-um-text">
          {this.props.title} is temporarily unavailable.
        </div>
      );
    }
    return this.props.children;
  }
}
