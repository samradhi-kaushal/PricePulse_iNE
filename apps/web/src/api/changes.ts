import { request } from "./client";
import type { ProductChange } from "../types";

export async function listChanges(): Promise<{ items: ProductChange[] }> {
  return request<{ items: ProductChange[] }>("/changes/");
}

export async function getTrackedProductChanges(id: string): Promise<{ items: ProductChange[] }> {
  return request<{ items: ProductChange[] }>(`/tracked-products/${id}/changes/`);
}
