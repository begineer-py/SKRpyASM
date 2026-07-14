import AppRouter from "./app/router";
import Providers from "./app/providers";
import { ErrorBoundary } from "./components/common";

function App() {
  return (
    <Providers>
      <ErrorBoundary>
        <AppRouter />
      </ErrorBoundary>
    </Providers>
  );
}

export default App;
