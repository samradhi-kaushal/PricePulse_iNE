import { request } from "./client";
import type { DashboardData } from "../types";

export async function getDashboard(): Promise<DashboardData> {
  return request<DashboardData>("/dashboard/");
}
