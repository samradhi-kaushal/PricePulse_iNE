import { request } from "./client";
import type { PricePoint } from "../types";

export async function getPriceHistory(trackedProductId: string): Promise<{ items: PricePoint[] }> {
  return request<{ items: PricePoint[] }>(`/tracked-products/${trackedProductId}/history/`);
}
