import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowUpRight, Check, ChevronLeft, ChevronRight, Copy, Pause, Play } from "lucide-react";
import lockup from "@/assets/logo-nav.png";
import karcastLogo from "@/assets/karcast.png";
import leafletLogo from "@/assets/leafletai.png";
import leafletInk from "@/assets/leafletai-ink.png";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { activities, email, premises, premisesPlain, products } from "@/lib/company";

const logos = {
  KarCast: { src: karcastLogo, altSrc: null, width: 1600, height: 349 },
  LeafletAI: { src: leafletInk, altSrc: leafletLogo, width: 1105, height: 224 },
} as const;

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return (
    <div id="top" className="min-h-screen">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-30 focus:rounded-full focus:bg-panel focus:px-4 focus:py-2"
      >
        Skip to content
      </a>
      <SiteHeader />
      <main id="content">
        <Hero />
        <Products />
        <Activities />
        <Premises />
      </main>
      <Footer />
    </div>
  );
}

function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-5 pb-16 pt-12 md:px-8 md:pb-24 md:pt-16">
      <p className="rise text-sm font-medium tracking-wide text-azure">Software, commerce, and brand</p>
      <h1 className="rise rise-2 mt-5 max-w-4xl font-display text-5xl font-medium leading-display tracking-display text-ink sm:text-7xl">
        Work that gets a response.
      </h1>
      <p className="rise rise-3 mt-6 max-w-xl text-lg text-muted">
        Responsyve makes KarCast and LeafletAI, and the licensed practice behind them: software,
        stores, sites, campaigns, and brands.
      </p>
      <div className="rise rise-3 mt-8 flex flex-wrap items-center gap-3">
        <Button asChild>
          <a href="#products">See the work</a>
        </Button>
        <Button asChild variant="secondary">
          <a href={`mailto:${email}`}>{email}</a>
        </Button>
      </div>
      <WorkBanner />
    </section>
  );
}

const bannerLogos = {
  KarCast: { src: karcastLogo, width: 1600, height: 349 },
  LeafletAI: { src: leafletLogo, width: 1105, height: 224 },
} as const;

function WorkBanner() {
  const slides = [
    ...activities.map((activity) => ({
      id: activity.title,
      kicker: "Practice",
      title: activity.title,
      line: activity.body,
      href: "#activities" as string | undefined,
      host: undefined as string | undefined,
      logo: undefined as "KarCast" | "LeafletAI" | undefined,
    })),
    ...products.map((product) => ({
      id: product.name,
      kicker: "Product",
      title: product.name,
      line: `${product.line}. ${product.body}`,
      href: product.href,
      host: product.host,
      logo: product.name,
    })),
  ];
  const count = slides.length;
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hover, setHover] = useState(false);
  const [reduced, setReduced] = useState(false);
  const slide = slides[index];
  const held = paused || hover || reduced;

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReduced(media.matches);
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);

  function go(next: number) {
    setIndex((next + count) % count);
  }

  return (
    <section
      className="rise rise-2 mt-12"
      aria-roledescription="carousel"
      aria-label="Responsyve work"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className={`relative overflow-hidden rounded-xl bg-night text-on-night ${held ? "is-paused" : ""}`}>
        <div key={slide.id} className="banner-in grid min-h-72 gap-8 p-6 md:min-h-80 md:grid-cols-12 md:p-10">
          <div className="flex flex-col md:col-span-7">
            <p className="text-sm font-medium tracking-wide text-on-night-muted">
              {String(index + 1).padStart(2, "0")} / {String(count).padStart(2, "0")} — {slide.kicker}
            </p>
            <h2 className="mt-4 max-w-xl font-display text-4xl font-medium leading-display tracking-display sm:text-5xl">
              {slide.title}
            </h2>
            <p className="mt-4 line-clamp-4 max-w-lg text-on-night-muted">{slide.line}</p>
            {slide.href ? (
              <a
                href={slide.href}
                {...(slide.host ? { target: "_blank", rel: "noreferrer" } : {})}
                className="mt-6 inline-flex min-h-11 items-center gap-2 self-start text-sm font-medium text-on-night hover:text-azure"
              >
                {slide.host ? slide.host : "The practice"}
                <ArrowUpRight aria-hidden="true" className="size-4" />
              </a>
            ) : null}
          </div>
          <div className="flex items-end md:col-span-5 md:justify-end">
            {slide.logo ? (
              <img
                src={bannerLogos[slide.logo].src}
                alt=""
                width={bannerLogos[slide.logo].width}
                height={bannerLogos[slide.logo].height}
                className="h-14 w-auto max-w-full sm:h-20"
              />
            ) : (
              <span className="font-display text-7xl font-medium leading-none tracking-display text-on-night opacity-20 sm:text-8xl" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between gap-3 px-4 py-3 md:px-6">
          <div className="flex gap-1">
            <Button
              type="button"
              variant="ghost"
              className="size-11 px-0 text-on-night hover:bg-night-2 hover:text-on-night"
              aria-label="Previous slide"
              onClick={() => go(index - 1)}
            >
              <ChevronLeft aria-hidden="true" className="size-5" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="size-11 px-0 text-on-night hover:bg-night-2 hover:text-on-night"
              aria-label={paused ? "Play slides" : "Pause slides"}
              aria-pressed={paused}
              onClick={() => setPaused((value) => !value)}
            >
              {paused ? <Play aria-hidden="true" className="size-4" /> : <Pause aria-hidden="true" className="size-4" />}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="size-11 px-0 text-on-night hover:bg-night-2 hover:text-on-night"
              aria-label="Next slide"
              onClick={() => go(index + 1)}
            >
              <ChevronRight aria-hidden="true" className="size-5" />
            </Button>
          </div>
        </div>
        {reduced ? null : (
          <div className="h-1 bg-night-2" aria-hidden="true">
            <div key={slide.id} className="banner-progress h-full bg-azure" onAnimationEnd={() => go(index + 1)} />
          </div>
        )}
      </div>
    </section>
  );
}

function Products() {
  return (
    <section id="products" className="border-t border-line">
      <div className="mx-auto max-w-6xl px-5 py-16 md:px-8 md:py-24">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 className="font-display text-4xl font-medium tracking-display sm:text-5xl">Selected work</h2>
          <p className="max-w-sm text-muted">Two products, each with its own site. The live offer sits there.</p>
        </div>
        <div className="mt-10 grid gap-4 lg:grid-cols-2">
          {products.map((product, index) => {
            const logo = logos[product.name];
            return (
            <a
              key={product.name}
              href={product.href}
              target="_blank"
              rel="noreferrer"
              className={
                index === 0
                  ? "group flex min-h-72 flex-col rounded-xl bg-night p-6 text-on-night transition-colors duration-150 hover:bg-night-2 md:p-8"
                  : "group flex min-h-72 flex-col rounded-xl border border-line bg-panel p-6 text-ink transition-colors duration-150 hover:bg-azure-soft md:p-8"
              }
            >
              <div className="flex items-center justify-between gap-4">
                <span className={index === 0 ? "text-sm font-medium text-on-night-muted" : "text-sm font-medium text-muted"}>
                  0{index + 1} — {product.host}
                </span>
                <ArrowUpRight
                  aria-hidden="true"
                  className="size-5 transition-transform duration-150 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                />
              </div>
              <div className="mt-auto pt-8">
                <h3>
                  <img
                    src={logo.src}
                    alt={product.name}
                    width={logo.width}
                    height={logo.height}
                    className={
                      logo.altSrc
                        ? "h-11 w-auto max-w-full dark:hidden sm:h-14"
                        : "h-12 w-auto max-w-full sm:h-16"
                    }
                  />
                  {logo.altSrc ? (
                    <img
                      src={logo.altSrc}
                      alt={product.name}
                      width={logo.width}
                      height={logo.height}
                      className="hidden h-11 w-auto max-w-full dark:block sm:h-14"
                    />
                  ) : null}
                </h3>
                <p className={index === 0 ? "mt-5 max-w-md font-display text-2xl font-medium tracking-tight text-on-night sm:text-3xl" : "mt-5 max-w-md font-display text-2xl font-medium tracking-tight text-ink sm:text-3xl"}>
                  {product.line}
                </p>
                <p className={index === 0 ? "mt-2 max-w-md text-on-night-muted" : "mt-2 max-w-md text-muted"}>
                  {product.body}
                </p>
                <p className="mt-5 text-sm font-medium">{product.meta}</p>
              </div>
            </a>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Activities() {
  return (
    <section id="activities" className="border-t border-line bg-panel">
      <div className="mx-auto max-w-6xl px-5 py-16 md:px-8 md:py-24">
        <h2 className="max-w-xl font-display text-4xl font-medium tracking-display sm:text-5xl">
          The practice we are licensed to carry out.
        </h2>
        <ol className="mt-12">
          {activities.map((activity, index) => (
            <li
              key={activity.title}
              className="grid gap-3 border-t border-line py-7 last:border-b md:grid-cols-12 md:items-start md:gap-8"
            >
              <span className="font-display text-sm tabular-nums text-muted md:col-span-1">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="font-display text-2xl font-medium tracking-tight md:col-span-4 sm:text-3xl">
                {activity.title}
              </h3>
              <div className="md:col-span-7">
                <p className="text-muted">{activity.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Premises() {
  const [status, setStatus] = useState<"idle" | "copied" | "selected">("idle");

  async function copyAddress() {
    const text = premisesPlain;
    let copied = false;
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
    } catch {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.focus();
      area.select();
      try {
        copied = document.execCommand("copy");
      } catch {
        copied = false;
      }
      area.remove();
      if (!copied) {
        const card = document.getElementById("address-card");
        if (card) {
          const range = document.createRange();
          range.selectNodeContents(card);
          const selection = window.getSelection();
          selection?.removeAllRanges();
          selection?.addRange(range);
        }
      }
    }
    setStatus(copied ? "copied" : "selected");
    window.setTimeout(() => setStatus("idle"), 2200);
  }

  const label =
    status === "copied" ? "Copied" : status === "selected" ? "Address selected" : "Copy address";

  return (
    <section id="premises" className="bg-night text-on-night">
      <div className="mx-auto grid max-w-6xl gap-12 px-5 py-16 md:px-8 md:py-24 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <p className="text-sm font-medium tracking-wide text-on-night-muted">Contact</p>
          <h2 className="mt-4 font-display text-4xl font-medium tracking-display sm:text-6xl">
            <a href={`mailto:${email}`} className="underline decoration-azure decoration-2 underline-offset-8 hover:text-azure">
              {email}
            </a>
          </h2>
          <p className="mt-6 max-w-md text-on-night-muted">
            Write for a product, a site, a campaign, or a brand. The studio is in Dubai, United Arab Emirates —
            floor 3, building A3, Business Park.
          </p>
        </div>
        <div className="lg:col-span-5">
          <dl id="address-card" className="grid gap-px overflow-hidden rounded-xl bg-night-2 sm:grid-cols-2">
            {premises.map((row) => (
              <div
                key={row.label}
                className={`bg-night px-5 py-5 ${row.label === "City" || row.label === "Country" ? "sm:col-span-2" : ""}`}
              >
                <dt className="text-sm font-medium text-on-night-muted">{row.label}</dt>
                <dd className="mt-1 font-display text-xl font-medium tracking-tight">{row.value}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-5">
            <Button type="button" variant="secondary" onClick={copyAddress}>
              {status === "idle" ? (
                <Copy aria-hidden="true" className="size-4" />
              ) : (
                <Check aria-hidden="true" className="size-4" />
              )}
              {label}
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-night-2 bg-night text-on-night">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 py-8 md:flex-row md:items-center md:justify-between md:px-8">
        <img src={lockup} alt="" width={800} height={200} className="h-10 w-auto sm:h-12" />
        <a href={`mailto:${email}`} className="inline-flex min-h-11 items-center text-sm font-medium hover:text-azure">
          {email}
        </a>
        <ul className="flex gap-6 text-sm">
          {products.map((product) => (
            <li key={product.host}>
              <a
                href={product.href}
                target="_blank"
                rel="noreferrer"
                className="inline-flex min-h-11 items-center font-medium text-on-night-muted hover:text-on-night"
              >
                {product.name}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </footer>
  );
}
