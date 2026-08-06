import { redirect } from "next/navigation";

// Sektör Rotasyonu is now a panel on Piyasa Pusulası (fewer tabs, one
// "how's the market" page) -- this route only exists so old bookmarks and
// muscle memory still land somewhere.
export default async function RotasyonRedirect({
  searchParams,
}: {
  searchParams: Promise<{ mine?: string }>;
}) {
  const { mine } = await searchParams;
  redirect(mine === "1" ? "/piyasa?mine=1" : "/piyasa");
}
