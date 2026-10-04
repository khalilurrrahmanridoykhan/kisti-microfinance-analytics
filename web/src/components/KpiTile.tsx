import { Icon, type IconName } from "./Icon";

const UNIT_SUFFIX = " taka";

/** A headline number. A trailing " taka" unit is set smaller than the figure so long currency
 * values still fit on one line in the narrow tile. */
export function KpiTile({
  label,
  value,
  title,
  detail,
  icon,
}: {
  label: string;
  value: string;
  title?: string;
  detail?: string;
  icon?: IconName;
}) {
  const hasUnit = value.endsWith(UNIT_SUFFIX);
  return (
    <div className="kpi-tile" title={title}>
      <div className="kpi-head">
        <div className="kpi-label">{label}</div>
        {icon && (
          <span className="kpi-icon">
            <Icon name={icon} size={18} />
          </span>
        )}
      </div>
      <div className="kpi-value">
        {hasUnit ? value.slice(0, -UNIT_SUFFIX.length) : value}
        {hasUnit && <span className="kpi-unit">{UNIT_SUFFIX}</span>}
      </div>
      {detail && <div className="kpi-detail">{detail}</div>}
    </div>
  );
}
