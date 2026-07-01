import { cookies } from "next/headers";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const API = process.env.API_INTERNAL_URL ?? "http://feedback-api:8101";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const cookieStore = await cookies();
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const idempotency = request.headers.get("idempotency-key");
  if (idempotency) headers.set("idempotency-key", idempotency);
  const session = cookieStore.get("feedback_demo_session")?.value;
  if (session) headers.set("x-demo-session", session);
  const body = request.method === "GET" ? undefined : await request.arrayBuffer();
  const response = await fetch(`${API}/${path.join("/")}${request.nextUrl.search}`, { method: request.method, headers, body, cache: "no-store" });
  const payload = await response.arrayBuffer();
  const outgoing = new NextResponse(payload, { status: response.status, headers: { "content-type": response.headers.get("content-type") ?? "application/json" } });
  if (path.join("/") === "v1/demo/sessions" && response.ok) {
    const parsed = JSON.parse(new TextDecoder().decode(payload));
    outgoing.cookies.set("feedback_demo_session", parsed.session_id, { httpOnly: true, sameSite: "lax", maxAge: 86400, path: "/feedback" });
  }
  return outgoing;
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;

