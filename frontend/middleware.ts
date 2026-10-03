
import { NextRequest, NextResponse } from "next/server";

const PUBLIC = new Set(["/", "/auth", "/api/session", "/favicon.ico"]);
const PROTECTED = ["/dashboard", "/opportunities", "/career-twin", "/resume", "/companies", "/interviews", "/applications", "/career-plan", "/settings"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (PUBLIC.has(pathname) || pathname.startsWith("/_next") || pathname.startsWith("/api/session/bootstrap")) return NextResponse.next();
  if (!PROTECTED.some((route) => pathname === route || pathname.startsWith(`${route}/`))) return NextResponse.next();

  const session = request.cookies.get("careerpilot_session")?.value;
  if (session) return NextResponse.next();

  const url = request.nextUrl.clone();
  url.pathname = "/auth";
  url.searchParams.set("next", pathname);
  return NextResponse.redirect(url);
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
