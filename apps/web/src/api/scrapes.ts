import { request } from "./client";
import type { Attempt } from "../types";

export async function getScrapeLogs(trackedProductId?: string): Promise<{ items: Attempt[] }> {
  const endpoint = trackedProductId ? `/tracked-products/${trackedProductId}/scrapes/` : "/scrapes/";
  return request<{ items: Attempt[] }>(endpoint);
}
