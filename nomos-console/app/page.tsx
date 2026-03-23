export default function Home() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>NomOS Console</h1>
      <p>AI Agent Fleet Management — EU AI Act Compliant</p>
      <div style={{ marginTop: '2rem', padding: '1rem', background: '#22c55e', color: 'white', borderRadius: '8px', display: 'inline-block', cursor: 'pointer', fontSize: '1.2rem' }}>
        Mitarbeiter einstellen
      </div>
      <div style={{ marginTop: '2rem' }}>
        <h2>Fleet Status</h2>
        <p>No agents deployed yet. Click the button above to hire your first AI employee.</p>
      </div>
    </main>
  )
}
