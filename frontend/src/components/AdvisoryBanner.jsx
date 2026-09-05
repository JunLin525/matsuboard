export default function AdvisoryBanner({ advisories }) {
  if (!advisories || advisories.length === 0) return null;

  return (
    <div className="advisory-banner">
      {advisories.map((a) => (
        <p key={a.type}>⚠️ {a.message}</p>
      ))}
    </div>
  );
}
