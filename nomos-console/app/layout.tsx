export const metadata = {
  title: 'NomOS Console',
  description: 'AI Agent Fleet Management — EU AI Act Compliant',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
