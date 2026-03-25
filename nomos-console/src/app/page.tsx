/**
 * NomOS Root Page — Redirects to login.
 * Users who are already authenticated will be redirected from /login to their dashboard.
 */
import { redirect } from 'next/navigation';

export default function RootPage() {
  redirect('/login');
}
