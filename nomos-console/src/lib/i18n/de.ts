/** Deutsche Uebersetzungen — NomOS Console */
export const de = {
  // Meta
  'app.title': 'NomOS — Ihr Team im Griff',
  'app.description': 'Compliance Control Plane fuer Ihre KI-Mitarbeiter',

  // Navigation — Mitarbeiter-Metapher
  'nav.dashboard': 'Uebersicht',
  'nav.myTeam': 'Mein Team',
  'nav.hire': 'Einstellen',
  'nav.approvals': 'Freigaben',
  'nav.costs': 'Kosten',
  'nav.compliance': 'Rechts-Check',
  'nav.audit': 'Protokoll',
  'nav.diagnostics': 'Gesundheitscheck',
  'nav.users': 'Nutzer',
  'nav.settings': 'Einstellungen',
  'nav.myAgents': 'Meine Mitarbeiter',
  'nav.tasks': 'Aufgaben',
  'nav.help': 'Hilfe',
  'nav.complianceReports': 'Compliance-Berichte',

  // Auth
  'auth.login': 'Anmelden',
  'auth.logout': 'Abmelden',
  'auth.email': 'E-Mail-Adresse',
  'auth.password': 'Passwort',
  'auth.submit': 'Anmelden',
  'auth.forgotPassword': 'Passwort vergessen?',
  'auth.loginTitle': 'Willkommen bei NomOS',
  'auth.loginSubtitle': 'Melden Sie sich an, um Ihr Team zu verwalten.',
  'auth.totpTitle': 'Zwei-Faktor-Authentifizierung',
  'auth.totpSubtitle': 'Geben Sie den 6-stelligen Code aus Ihrer Authenticator-App ein.',
  'auth.totpLabel': 'Authentifizierungscode',
  'auth.totpSubmit': 'Bestaetigen',
  'auth.invalidCredentials': 'E-Mail oder Passwort ist falsch. Bitte versuchen Sie es erneut.',
  'auth.accountLocked': 'Ihr Konto wurde gesperrt. Bitte warten Sie 15 Minuten oder kontaktieren Sie den Administrator.',
  'auth.totpInvalid': 'Der eingegebene Code ist ungueltig. Bitte pruefen Sie Ihre Authenticator-App.',
  'auth.sessionExpired': 'Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.',

  // Header
  'header.theme.light': 'Heller Modus',
  'header.theme.dark': 'Dunkler Modus',
  'header.theme.toggle': 'Farbschema wechseln',
  'header.lang.toggle': 'Sprache wechseln',
  'header.user.menu': 'Benutzermenue',
  'header.user.profile': 'Mein Profil',
  'header.user.settings': 'Einstellungen',

  // Common Actions
  'action.retry': 'Erneut versuchen',
  'action.cancel': 'Abbrechen',
  'action.save': 'Speichern',
  'action.delete': 'Loeschen',
  'action.edit': 'Bearbeiten',
  'action.create': 'Erstellen',
  'action.close': 'Schliessen',
  'action.confirm': 'Bestaetigen',
  'action.back': 'Zurueck',
  'action.next': 'Weiter',
  'action.search': 'Suchen',
  'action.filter': 'Filtern',
  'action.export': 'Exportieren',
  'action.contactAdmin': 'Administrator kontaktieren',

  // Status — Mitarbeiter-Metapher
  'status.online': 'Aktiv',
  'status.paused': 'Pausiert',
  'status.offline': 'Offline',
  'status.killed': 'Gekuendigt',
  'status.deploying': 'Einarbeitung',
  'status.error': 'Gestoert',

  // Errors — Brand Voice: direkt, ehrlich, hilfreich
  'error.title': 'Etwas ist schiefgegangen',
  'error.description': 'Ein unerwarteter Fehler ist aufgetreten. Unser Team wurde benachrichtigt.',
  'error.network': 'Die Verbindung zum Server ist unterbrochen. Pruefen Sie Ihre Netzwerkverbindung.',
  'error.notFound': 'Diese Seite wurde nicht gefunden.',
  'error.forbidden': 'Sie haben keine Berechtigung fuer diese Aktion.',
  'error.serverError': 'Der Server konnte die Anfrage nicht verarbeiten. Bitte versuchen Sie es spaeter erneut.',
  'error.timeout': 'Die Anfrage hat zu lange gedauert. Bitte versuchen Sie es erneut.',
  'error.validation': 'Bitte ueberpruefen Sie Ihre Eingaben.',
  'error.reportSent': 'Der Fehler wurde automatisch gemeldet.',

  // Empty States — hilfreich mit CTA
  'empty.team': 'Noch keine Mitarbeiter eingestellt.',
  'empty.teamCta': 'Jetzt einstellen',
  'empty.tasks': 'Keine offenen Aufgaben.',
  'empty.tasksCta': 'Aufgabe erstellen',
  'empty.approvals': 'Keine ausstehenden Freigaben.',
  'empty.audit': 'Noch keine Protokolleintraege vorhanden.',
  'empty.generic': 'Hier ist noch nichts zu sehen.',

  // Loading
  'loading.default': 'Wird geladen...',
  'loading.team': 'Team wird geladen...',
  'loading.data': 'Daten werden abgerufen...',

  // Table
  'table.noResults': 'Keine Ergebnisse gefunden.',
  'table.sortAsc': 'Aufsteigend sortieren',
  'table.sortDesc': 'Absteigend sortieren',

  // Toast
  'toast.success': 'Erfolgreich',
  'toast.error': 'Fehler',
  'toast.warning': 'Warnung',
  'toast.info': 'Hinweis',

  // Accessibility
  'a11y.skipToContent': 'Zum Hauptinhalt springen',
  'a11y.mainContent': 'Hauptinhalt',
  'a11y.navigation': 'Hauptnavigation',
  'a11y.closeDialog': 'Dialog schliessen',
  'a11y.openMenu': 'Menue oeffnen',
  'a11y.closeMenu': 'Menue schliessen',
  'a11y.logoAlt': 'NomOS Adler-Logo',
  'a11y.required': 'Pflichtfeld',
} as const;

export type TranslationKey = keyof typeof de;
