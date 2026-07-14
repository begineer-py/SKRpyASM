import AppRouter from "./app/router";
import Providers from "./app/providers";

function App() {
  return (
    <Providers>
      <AppRouter />
    </Providers>
  );
}

export default App;
