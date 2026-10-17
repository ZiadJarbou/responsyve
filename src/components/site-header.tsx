import { useState } from "react";
import { Menu, Moon, Sun, X } from "lucide-react";
import { email } from "@/lib/company";

const links = [
  { href: "#products", label: "Work" },
  { href: "#activities", label: "Practice" },
  { href: "#premises", label: "Studio" },
];

function applyTheme(dark: boolean) {
  document.documentElement.classList.toggle("dark", dark);
  localStorage.setItem("responsyve-theme", dark ? "dark" : "light");
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", dark ? "#101216" : "#f3f1ec");
}

function ThemeToggle() {
  return (
    <button
      type="button"
      aria-label="Toggle color theme"
      className="inline-flex size-11 items-center justify-center rounded-full text-on-night hover:bg-night-2"
      onClick={() => applyTheme(!document.documentElement.classList.contains("dark"))}
    >
      <Sun className="hidden size-5 dark:block" aria-hidden="true" />
      <Moon className="size-5 dark:hidden" aria-hidden="true" />
    </button>
  );
}

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 border-b border-night-2 bg-night text-on-night">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 md:px-8">
        <a href="#top" className="font-display text-xl font-medium tracking-tight text-on-night sm:text-2xl">
          Responsyve
        </a>
        <div className="flex items-center gap-1">
          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="inline-flex min-h-11 items-center rounded-full px-4 text-sm font-medium text-on-night hover:bg-night-2"
              >
                {link.label}
              </a>
            ))}
            <a
              href={`mailto:${email}`}
              className="ml-2 inline-flex min-h-11 items-center rounded-full bg-on-night px-5 text-sm font-medium text-night hover:bg-azure-soft hover:text-ink"
            >
              Contact
            </a>
          </nav>
          <ThemeToggle />
          <button
            type="button"
            className="inline-flex size-11 items-center justify-center rounded-full text-on-night hover:bg-night-2 md:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
            <span className="sr-only">{open ? "Close menu" : "Open menu"}</span>
          </button>
        </div>
      </div>
      {open ? (
        <nav id="mobile-nav" className="border-t border-night-2 px-4 py-2 md:hidden" aria-label="Primary">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="flex min-h-11 items-center text-base font-medium text-on-night"
              onClick={() => setOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <a
            href={`mailto:${email}`}
            className="flex min-h-11 items-center text-base font-medium text-on-night"
            onClick={() => setOpen(false)}
          >
            {email}
          </a>
        </nav>
      ) : null}
    </header>
  );
}
