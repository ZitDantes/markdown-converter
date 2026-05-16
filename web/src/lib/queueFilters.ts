import type { FileQueueItem } from "@shared/bridge-contract";
import { normalizeFilterExtension } from "./formatColors";

export function countsByExtension(items: FileQueueItem[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const item of items) {
    const key = normalizeFilterExtension(item.extension);
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
}

export function filterQueueItems(
  items: FileQueueItem[],
  activeExtensions: ReadonlySet<string>,
  searchQuery: string,
): FileQueueItem[] {
  const q = searchQuery.trim().toLowerCase();
  return items.filter((item) => {
    const ext = normalizeFilterExtension(item.extension);
    if (activeExtensions.size > 0 && !activeExtensions.has(ext)) {
      return false;
    }
    if (q && !item.fileName.toLowerCase().includes(q)) {
      return false;
    }
    return true;
  });
}
