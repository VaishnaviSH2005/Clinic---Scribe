import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ACCESS_TOKEN_COOKIE = "cliniscribe_access";
const PUBLIC_ROUTES = ["/login", "/forgot-password", "/reset-password"];

/**
 * Fast-path route protection (PRD Ch19 — Protected Route Guard). This is a
 * UX optimization only: it redirects based on cookie *presence*, never
 * validates the token. The backend is the sole authority on whether a
 * session is actually valid (Ch7.1/Ch19) — every API call still goes
 * through full server-side validation regardless of what this middleware
 * decides.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSessionCookie = request.cookies.has(ACCESS_TOKEN_COOKIE);
  const isPublicRoute = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));

  if (!hasSessionCookie && !isPublicRoute && pathname !== "/") {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (hasSessionCookie && isPublicRoute) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
