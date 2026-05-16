/**
 * Next.js Edge Middleware — route protection.
 *
 * Uses the presence of Django's `sessionid` cookie as a lightweight
 * authentication signal.  The authoritative check is always the backend;
 * middleware only prevents unnecessary page loads and improves UX.
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that authenticated users should be redirected AWAY from.
const AUTH_ONLY_PATHS = ["/login", "/register"];

// Routes that REQUIRE authentication (prefix-matched).
const PROTECTED_PREFIXES = ["/dashboard", "/settings", "/onboarding"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get("sessionid");
  const isAuthenticated = Boolean(sessionCookie?.value);

  // --- Authenticated user hitting an auth-only page → dashboard ---
  if (isAuthenticated && AUTH_ONLY_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // --- Unauthenticated user hitting a protected page → login ---
  const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
  if (!isAuthenticated && isProtected) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

// Only run middleware on navigable routes — skip API, static assets, etc.
export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|public).*)",
  ],
};
