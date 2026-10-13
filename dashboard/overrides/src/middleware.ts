import { NextResponse, type NextRequest } from "next/server";
import { LANG_CODES, DEFAULT_LANG } from "@/lib/i18n";

// ─────────────────────────────────────────────────────────────────────────
// i18n routing (task A2, plan.md D5) — the standard "default locale
// unprefixed, others prefixed" pattern implemented as a REWRITE, not a
// redirect, so the public URL stays unprefixed for the default language
// (cs) while the actual route tree underneath only ever has to handle
// `/[lang]/[city]/...` with `lang` always present.
//
// This is a routing-layer decision made before the route matches — it does
// NOT call cookies() or read any per-request state, so it does not force
// dynamic rendering the way the old cookie-based getLang() did (audit T8).
// Next.js can still serve a statically-generated page through the rewrite.
//
//   /praha            -(rewrite)->  /cs/praha             (internal only)
//   /praha/members     -(rewrite)->  /cs/praha/members     (internal only)
//   /en/praha           (already shaped correctly)          -> no rewrite
//   /cs/praha           -(308 redirect)->  /praha           (canonicalize away
//                                                             from the default
//                                                             language's own
//                                                             prefix, so there
//                                                             is exactly one
//                                                             canonical cs URL)
// ─────────────────────────────────────────────────────────────────────────

const NON_DEFAULT_LANG_CODES = LANG_CODES.filter((c) => c !== DEFAULT_LANG);

function firstSegment(pathname: string): string | undefined {
  return pathname.split("/")[1];
}

function isAssetPath(pathname: string): boolean {
  if (pathname.startsWith("/api/") || pathname === "/api") return true;
  if (pathname.startsWith("/.well-known/")) return true;
  // Any path segment with a file extension (favicon.svg, robots.txt,
  // sitemap.xml, llms.txt, *.md, opengraph-image, etc.) is a static/
  // generated asset, not a localized app page.
  const last = pathname.split("/").pop() ?? "";
  return last.includes(".");
}

// ─── Markdown content-negotiation + AI-discovery headers (from A1, kept as
// generic site-wide behaviour) ──────────────────────────────────────────────
// Scoped to the two truly site-global pages ("/" and "/about" — the default-
// language, unprefixed URLs). Per-city pages (/praha, /praha/members, ...)
// don't have one universal markdown mirror to negotiate against (there are
// now as many as there are cities x languages) — extending this to those is
// left for a future task (A3/A4), not part of A2's routing-mechanism scope.
const markdownAlternates = new Map([
  ["/", "/index.md"],
  ["/about", "/about.md"],
]);

const linkHeader = [
  '</.well-known/agent-skills/index.json>; rel="index"; type="application/json"; title="Agent Skills"',
  '</llms.txt>; rel="alternate"; type="text/plain"; title="LLM Context"',
  '</sitemap.xml>; rel="sitemap"; type="application/xml"',
  '</robots.txt>; rel="alternate"; type="text/plain"; title="Robots"',
].join(", ");

function withAiDiscoveryHeaders(response: NextResponse) {
  response.headers.set("Link", linkHeader);
  return response;
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname.replace(/\/$/, "") || "/";

  if (isAssetPath(pathname)) {
    return withAiDiscoveryHeaders(NextResponse.next());
  }

  const seg1 = firstSegment(pathname);

  // Explicit default-lang prefix ("/cs", "/cs/praha", ...) -> redirect to
  // the unprefixed canonical URL. Keeps exactly one indexable URL per page.
  if (seg1 === DEFAULT_LANG) {
    const rest = pathname.slice(`/${DEFAULT_LANG}`.length) || "/";
    const url = request.nextUrl.clone();
    url.pathname = rest;
    return NextResponse.redirect(url, 308);
  }

  // Already has a valid non-default language prefix ("/en/praha", ...) ->
  // matches the [lang]/[city] route tree as-is, no rewrite needed.
  if (seg1 && NON_DEFAULT_LANG_CODES.includes(seg1)) {
    return handleMarkdownAndDiscovery(request, pathname);
  }

  // Default-language votes have an explicit route so on-demand ISR keys
  // match the public path. Rewriting an unbuilt vote path disables the
  // full-route cache in the deployed Next.js 15.5 runtime.
  if (/^\/[^/]+\/vote-event\/[^/]+$/.test(pathname)) {
    return withAiDiscoveryHeaders(NextResponse.next());
  }

  // No language prefix at all -> internally rewrite to the default language
  // so the actual route tree only ever sees `/[lang]/...`. The browser URL
  // bar / usePathname() still show the unprefixed path.
  const rewriteUrl = request.nextUrl.clone();
  rewriteUrl.pathname = `/${DEFAULT_LANG}${pathname === "/" ? "" : pathname}`;
  const response = NextResponse.rewrite(rewriteUrl);
  return applyMarkdownAndDiscovery(request, pathname, response);
}

function handleMarkdownAndDiscovery(request: NextRequest, pathname: string) {
  return applyMarkdownAndDiscovery(request, pathname, NextResponse.next());
}

function applyMarkdownAndDiscovery(request: NextRequest, pathname: string, response: NextResponse) {
  const wantsMarkdown = request.headers.get("accept")?.includes("text/markdown");
  const markdownPath = markdownAlternates.get(pathname);

  if (wantsMarkdown && markdownPath) {
    const url = request.nextUrl.clone();
    url.pathname = markdownPath;
    return withAiDiscoveryHeaders(NextResponse.rewrite(url));
  }

  return withAiDiscoveryHeaders(response);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.svg).*)"],
};
