import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import { contentTypeFor, resolveResultsPath } from "@/lib/server/results";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params;
    const rel = path.join("/");
    const target = resolveResultsPath(rel);
    const data = await fs.readFile(target);
    return new NextResponse(data, {
      status: 200,
      headers: { "content-type": contentTypeFor(target) },
    });
  } catch {
    return NextResponse.json({ error: "file_not_found" }, { status: 404 });
  }
}
