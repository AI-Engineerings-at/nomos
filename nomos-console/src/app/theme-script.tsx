/**
 * NomOS Theme Script — Prevents FOUC (Flash of Unstyled Content).
 * Reads theme from localStorage or OS preference BEFORE React hydrates.
 * Content is a static string literal — no user input, no XSS risk.
 */

// This static string is safe: it reads only from localStorage and matchMedia,
// both controlled by the user's own browser. No external or untrusted input.
const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem('nomos-theme');if(!t){t=window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'}document.documentElement.setAttribute('data-theme',t);var l=localStorage.getItem('nomos-lang');if(l==='en')document.documentElement.lang='en'}catch(e){}})()`;

export function ThemeScript() {
  // Static content only — no dynamic values, no user input
  return (
    <script
      // eslint-disable-next-line react/no-danger -- Static constant, safe
      dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }}
    />
  );
}
