export default function FerryBoard({ ferries, error }) {
  if (error) {
    return (
      <section>
        <h2>船班資訊（台馬之星）</h2>
        <p className="error">載入失敗：{error.message}</p>
      </section>
    );
  }

  if (!ferries) {
    return (
      <section>
        <h2>船班資訊（台馬之星）</h2>
        <p>載入中...</p>
      </section>
    );
  }

  if (ferries.length === 0) {
    return (
      <section>
        <h2>船班資訊（台馬之星）</h2>
        <p>目前沒有資料。</p>
      </section>
    );
  }

  return (
    <section>
      <h2>船班資訊（台馬之星）</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>航線</th>
              <th>出發港</th>
              <th>航行順序</th>
              <th>開船時間</th>
              <th>狀態</th>
              <th>備註</th>
            </tr>
          </thead>
          <tbody>
            {ferries.map((f) => (
              <tr key={f.route} className={f.status?.includes("停航") ? "cancelled" : ""}>
                <td>{f.route}</td>
                <td>{f.depart_port}</td>
                <td>{f.arrive_order}</td>
                <td>{f.sched_depart_time}</td>
                <td>{f.status}</td>
                <td>
                  {f.note ? (
                    <a href={f.source_url} target="_blank" rel="noreferrer">
                      {f.note}
                    </a>
                  ) : (
                    ""
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
