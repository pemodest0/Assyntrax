import { NextResponse } from "next/server";
import { listLatestFiles, readLatestFile } from "@/lib/server/data";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const file = searchParams.get("file");
  if (file) {
    try {
      const data = await readLatestFile(file);
      return NextResponse.json(data);
    } catch {
      return NextResponse.json({ error: "file_not_found", file }, { status: 404 });
    }
  }
  const files = await listLatestFiles();
  return NextResponse.json({ files });
}
