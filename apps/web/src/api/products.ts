import { request } from "./client";
import type { Product } from "../types";

export async function listProducts(query?: string): Promise<{ items: Product[] }> {
  const q = query ? `?q=${encodeURIComponent(query)}` : "";
  return request<{ items: Product[] }>(`/products/${q}`);
}

export async function getProduct(id: string): Promise<Product> {
  return request<Product>(`/products/${id}/`);
}
