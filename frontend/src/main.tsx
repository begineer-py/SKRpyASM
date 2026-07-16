if (import.meta.env.DEV) {
  const { scan } = await import('react-scan');

  await import('react-grab');
  scan({ enabled: true });
}

const [{ default: ReactDOM }, { default: App }] = await Promise.all([
  import('react-dom/client'),
  import('./App.tsx'),
]);

await import('./global.css');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />,
);
