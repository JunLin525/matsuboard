function groupFlights(flights) {
  const grouped = {};
  for (const f of flights) {
    const key = `${f.airport}-${f.direction}`;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(f);
  }
  return grouped;
}

export default function FlightBoard({ flights, error }) {
  if (error) {
    return (
      <section>
        <h2>飛機動態</h2>
        <p className="error">載入失敗：{error.message}</p>
      </section>
    );
  }

  if (!flights) {
    return (
      <section>
        <h2>飛機動態</h2>
        <p>載入中...</p>
      </section>
    );
  }

  if (flights.length === 0) {
    return (
      <section>
        <h2>飛機動態</h2>
        <p>目前沒有資料。</p>
      </section>
    );
  }

  const grouped = groupFlights(flights);

  return (
    <section>
      <h2>飛機動態</h2>
      {Object.entries(grouped).map(([key, rows]) => (
        <div className="board-group" key={key}>
          <h3>
            {rows[0].airport_label} - {rows[0].direction_label}
          </h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>表定時間</th>
                  <th>預定/實際</th>
                  <th>航班</th>
                  <th>對方站</th>
                  <th>機型</th>
                  <th>狀態</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((f) => (
                  <tr key={f.flight_no} className={f.status?.includes("取消") ? "cancelled" : ""}>
                    <td>{f.sched_time}</td>
                    <td>{f.actual_time}</td>
                    <td>
                      {f.airline} {f.flight_no}
                    </td>
                    <td>{f.other_airport}</td>
                    <td>{f.aircraft_type}</td>
                    <td>{f.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </section>
  );
}
