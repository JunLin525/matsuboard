import { useEffect, useRef, useState } from "react";

/**
 * 定時呼叫 fetchFn 並回傳最新資料。後端本身刷新頻率是分鐘等級，
 * 所以這裡用簡單輪詢就夠，不需要 SSE/WebSocket。
 */
export function usePolling(fetchFn, intervalMs, deps) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const result = await fetchFn();
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err);
      }
    }

    load();
    timerRef.current = setInterval(load, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error };
}
