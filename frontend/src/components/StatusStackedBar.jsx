import { useState } from "react";

// 依 dataviz 規範的 mark spec：長條 <=24px、頂端 4px 圓角、底部方正貼齊基線、
// 堆疊區塊間留 2px surface 間隙。狀態色沿用 status palette（good/warning/critical），
// 不落在既定四色以內的狀態(例如尚無資料)歸類為 other，用 muted 灰。
const SEGMENTS = [
  { key: "good", label: "準時/已飛/已到", color: "var(--status-good)" },
  { key: "warning", label: "延誤", color: "var(--status-warning)" },
  { key: "critical", label: "取消", color: "var(--status-critical)" },
  { key: "other", label: "其他/未知", color: "var(--status-other)" },
];

const WIDTH = 320;
const HEIGHT = 200;
const PAD = { top: 14, right: 10, bottom: 26, left: 28 };
const CHART_W = WIDTH - PAD.left - PAD.right;
const CHART_H = HEIGHT - PAD.top - PAD.bottom;
const BAR_MAX = 24;
const GAP = 2;

function niceMax(value) {
  if (value <= 0) return 4;
  const step = value <= 10 ? 2 : value <= 20 ? 5 : value <= 50 ? 10 : 20;
  return Math.ceil(value / step) * step;
}

function roundedTopPath(x, y, w, h, r) {
  if (h <= 0) return "";
  const rr = Math.min(r, w / 2, h);
  return `M${x},${y + h} L${x},${y + rr} Q${x},${y} ${x + rr},${y} L${x + w - rr},${y} Q${x + w},${y} ${x + w},${y + rr} L${x + w},${y + h} Z`;
}

function formatDateLabel(iso) {
  const [, m, d] = iso.split("-");
  return `${Number(m)}/${Number(d)}`;
}

export default function StatusStackedBar({ title, data }) {
  const [hoverIndex, setHoverIndex] = useState(null);

  const hasAnyData = data.some((d) => d.total > 0);
  const yMax = niceMax(Math.max(...data.map((d) => d.total), 0));
  const bandWidth = CHART_W / data.length;
  const barWidth = Math.min(BAR_MAX, bandWidth * 0.55);
  const yTicks = [0, Math.round(yMax / 2), yMax];

  function scaleY(value) {
    return (value / yMax) * CHART_H;
  }

  return (
    <div className="stats-chart">
      <div className="stats-chart-head">
        <h3>{title}</h3>
        <span className="stats-chart-sub">最近 {data.length} 天航班狀態</span>
      </div>

      {!hasAnyData ? (
        <p className="stats-empty">這幾天還沒有航班資料。</p>
      ) : (
        <>
          <svg
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            role="img"
            aria-label={`${title}最近${data.length}天航班狀態堆疊長條圖`}
            className="stats-svg"
          >
            {/* y 軸格線 + 刻度 */}
            {yTicks.map((tick) => {
              const y = PAD.top + CHART_H - scaleY(tick);
              return (
                <g key={tick}>
                  <line
                    x1={PAD.left}
                    x2={WIDTH - PAD.right}
                    y1={y}
                    y2={y}
                    stroke="var(--chart-grid)"
                    strokeWidth="1"
                  />
                  <text x={PAD.left - 6} y={y} dy="0.32em" textAnchor="end" className="stats-axis-label">
                    {tick}
                  </text>
                </g>
              );
            })}

            {/* 基線 */}
            <line
              x1={PAD.left}
              x2={WIDTH - PAD.right}
              y1={PAD.top + CHART_H}
              y2={PAD.top + CHART_H}
              stroke="var(--chart-axis)"
              strokeWidth="1"
            />

            {data.map((d, i) => {
              const bandX = PAD.left + i * bandWidth;
              const barX = bandX + (bandWidth - barWidth) / 2;
              const baseline = PAD.top + CHART_H;

              let cursor = baseline;
              const nonZero = SEGMENTS.filter((s) => d[s.key] > 0);
              const segRects = [];

              nonZero.forEach((seg, segIdx) => {
                const h = scaleY(d[seg.key]);
                const isTop = segIdx === nonZero.length - 1;
                const y = cursor - h;
                segRects.push(
                  isTop ? (
                    <path key={seg.key} d={roundedTopPath(barX, y, barWidth, h, 4)} fill={seg.color} />
                  ) : (
                    <rect key={seg.key} x={barX} y={y} width={barWidth} height={h} fill={seg.color} />
                  )
                );
                cursor = y - GAP;
              });

              return (
                <g key={d.date}>
                  {/* 整條 hit target 比長條本身寬，滑到date那一欄都能觸發 tooltip */}
                  <rect
                    x={bandX}
                    y={PAD.top}
                    width={bandWidth}
                    height={CHART_H}
                    fill="transparent"
                    className={hoverIndex === i ? "stats-hit stats-hit-active" : "stats-hit"}
                    tabIndex={0}
                    onMouseEnter={() => setHoverIndex(i)}
                    onMouseLeave={() => setHoverIndex((h) => (h === i ? null : h))}
                    onFocus={() => setHoverIndex(i)}
                    onBlur={() => setHoverIndex((h) => (h === i ? null : h))}
                  />
                  {segRects}
                  <text
                    x={bandX + bandWidth / 2}
                    y={HEIGHT - 8}
                    textAnchor="middle"
                    className="stats-axis-label"
                  >
                    {formatDateLabel(d.date)}
                  </text>
                </g>
              );
            })}
          </svg>

          {hoverIndex !== null && (
            <div className="stats-tooltip" role="status">
              <strong>{formatDateLabel(data[hoverIndex].date)}</strong>
              <ul>
                {SEGMENTS.map((seg) => (
                  <li key={seg.key}>
                    <span className="stats-tooltip-key" style={{ borderColor: seg.color }} />
                    {seg.label}：<strong>{data[hoverIndex][seg.key]}</strong>
                  </li>
                ))}
                <li className="stats-tooltip-total">共 {data[hoverIndex].total} 班</li>
              </ul>
            </div>
          )}

          <ul className="stats-legend">
            {SEGMENTS.map((seg) => (
              <li key={seg.key}>
                <span className="stats-legend-swatch" style={{ background: seg.color }} />
                {seg.label}
              </li>
            ))}
          </ul>

          {/* 純文字表格版本，確保不用看圖也能拿到一樣的數字 */}
          <details className="stats-table-details">
            <summary>顯示表格</summary>
            <table className="stats-table">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>準時/已飛/已到</th>
                  <th>延誤</th>
                  <th>取消</th>
                  <th>其他</th>
                  <th>合計</th>
                </tr>
              </thead>
              <tbody>
                {data.map((d) => (
                  <tr key={d.date}>
                    <td>{formatDateLabel(d.date)}</td>
                    <td>{d.good}</td>
                    <td>{d.warning}</td>
                    <td>{d.critical}</td>
                    <td>{d.other}</td>
                    <td>{d.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      )}
    </div>
  );
}
