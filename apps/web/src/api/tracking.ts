import { request } from "./client";
import type { TrackedProduct } from "../types";

export async function listTrackedProducts(): Promise<{ items: TrackedProduct[] }> {
  return request<{ items: TrackedProduct[] }>("/tracked-products/");
}

export async function trackProduct(productId: string): Promise<TrackedProduct> {
  return request<TrackedProduct>("/tracked-products/", {
    method: "POST",
    body: JSON.stringify({ product_id: productId }),
  });
}

export async function stopTracking(id: string): Promise<void> {
  return request<void>(`/tracked-products/${id}/`, {
    method: "DELETE",
  });
}

export async function updateTrackedProductInterval(id: string, hours: number): Promise<TrackedProduct> {
  return request<TrackedProduct>(`/tracked-products/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ scrape_interval_hours: hours }),
  });
}

export async function manualScrape(id: string): Promise<{ scrape_result: any; tracked_product: TrackedProduct }> {
  return request<{ scrape_result: any; tracked_product: TrackedProduct }>(`/tracked-products/${id}/scrape/`, {
    method: "POST",
  });
}

