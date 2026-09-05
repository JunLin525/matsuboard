import { useState } from "react";

import { getAdvisory, getFerries, getFlights, getStats } from "./api";
import AdvisoryBanner from "./components/AdvisoryBanner";
import FerryBoard from "./components/FerryBoard";
import FlightBoard from "./components/FlightBoard";
import StatusStackedBar from "./components/StatusStackedBar";
import { usePolling } from "./hooks/usePolling";

const POLL_INTERVAL_MS = 60_000;
const STATS_DAYS = 3;

// 不用 toISOString()：那個固定回傳 UTC 時間，會跟看板的台灣時間對不上
// （凌晨 0-8 點會顯示成昨天）。用 Intl 明確指定 Asia/Taipei，跟後端算
// 「今天」的邏輯一致（見 common/timeutil.py 的 today_taipei()）。
const TAIPEI_DATE_FORMATTER = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Taipei" });

function todayISO() {
  return TAIPEI_DATE_FORMATTER.format(new Date());
}

export default function App() {
  const [date, setDate] = useState(todayISO());

  const { data: flightsData, error: flightsError } = usePolling(
    () => getFlights(date),
    POLL_INTERVAL_MS,
    [date]
  );
  const { data: ferriesData, error: ferriesError } = usePolling(
    () => getFerries(date),
    POLL_INTERVAL_MS,
    [date]
  );
  const { data: advisoryData } = usePolling(() => getAdvisory(date), POLL_INTERVAL_MS, [date]);
  const { data: statsData } = usePolling(() => getStats(STATS_DAYS), POLL_INTERVAL_MS, []);

  const statsByAirport = (statsData?.stats || []).reduce((acc, row) => {
    (acc[row.airport] ||= []).push(row);
    return acc;
  }, {});

  return (
    <div className="app">
      <header className="app-header">
        <h1>MatsuBoard 馬祖動態看板</h1>
        <label>
          日期
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
      </header>

      <AdvisoryBanner advisories={advisoryData?.advisories} />

      <main>
        {statsData && (
          <section className="stats-section">
            <h2>近 {STATS_DAYS} 天航班狀態趨勢</h2>
            <div className="stats-grid">
              <StatusStackedBar title="南竿" data={statsByAirport.LZN || []} />
              <StatusStackedBar title="北竿" data={statsByAirport.MFK || []} />
            </div>
          </section>
        )}

        <FlightBoard flights={flightsData?.flights} error={flightsError} />
        <FerryBoard ferries={ferriesData?.ferries} error={ferriesError} />
      </main>

      <footer className="app-footer">
        資料僅供參考，正確資訊請以民航局、台馬之星官方公告為準。
      </footer>
    </div>
  );
}
