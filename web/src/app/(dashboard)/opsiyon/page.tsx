import { redirect } from "next/navigation";

// Opsiyon Radarı is now a panel on Piyasa Pusulası (fewer tabs, one "how's
// the market" page) -- this route only exists so old bookmarks and muscle
// memory still land somewhere.
export default function OpsiyonRedirect() {
  redirect("/piyasa");
}
