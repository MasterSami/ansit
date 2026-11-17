/** Theme preference: follow the system, or force dark / light. */

export type ThemeChoice = "system" | "dark" | "light";

export const THEME_KEY = "ansit.theme";

export function readTheme(): ThemeChoice {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    return stored === "dark" || stored === "light" ? stored : "system";
  } catch {
    return "system";
  }
}

export function applyTheme(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", choice);
  try {
    if (choice === "system") localStorage.removeItem(THEME_KEY);
    else localStorage.setItem(THEME_KEY, choice);
  } catch {
    // storage blocked: the choice lasts for this page only
  }
}

/**
 * Runs before first paint (inlined in <head>) so a stored choice never flashes
 * the other theme.
 */
export const THEME_BOOTSTRAP = `try{var t=localStorage.getItem(${JSON.stringify(
  THEME_KEY,
)});if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}`;
