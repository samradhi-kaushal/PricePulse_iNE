import { request } from "./client";
import type { AlertItem } from "../types";

export async function listAlerts(unreadOnly: boolean = false): Promise<{ items: AlertItem[] }> {
  const query = unreadOnly ? "?unread=true" : "";
  return request<{ items: AlertItem[] }>(`/alerts/${query}`);
}

export async function getUnreadAlertCount(): Promise<{ unread_count: number }> {
  return request<{ unread_count: number }>("/alerts/unread-count/");
}

export async function markAlertRead(id: string): Promise<AlertItem> {
  return request<AlertItem>(`/alerts/${id}/read/`, {
    method: "POST",
  });
}

export async function markAllAlertsRead(): Promise<{ marked_read: number }> {
  return request<{ marked_read: number }>("/alerts/read-all/", {
    method: "POST",
  });
}
