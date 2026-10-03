
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!base) return NextResponse.json({ error: "NEXT_PUBLIC_API_BASE_URL is not configured." }, { status: 503 });

  const upstream = await fetch(`${base}/career-twin/session`, {
    method: "GET",
    headers: { "X-Request-ID": crypto.randomUUID() },
    cache: "no-store",
    credentials: "include",
  });

  const next = request.nextUrl.searchParams.get("next") || "/dashboard";
  const response = NextResponse.redirect(new URL(next, request.url));
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) response.headers.set("set-cookie", setCookie);
  return response;
}
