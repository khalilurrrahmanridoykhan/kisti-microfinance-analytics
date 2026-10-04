/** A titled dashboard panel. `index` renders the section number as a badge so the numbering
 * matches RESULTS.md without being part of the heading text. */
export function SectionCard({
  index,
  id,
  eyebrow,
  title,
  lead,
  className,
  children,
}: {
  index?: number;
  id?: string;
  eyebrow?: string;
  title: string;
  lead?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className={`card${className ? ` ${className}` : ""}`}>
      <header className="card-header">
        {index !== undefined && (
          <span className="card-index" aria-hidden="true">
            {String(index).padStart(2, "0")}
          </span>
        )}
        <div>
          {eyebrow && <p className="card-eyebrow">{eyebrow}</p>}
          <h2>
            {index !== undefined && <span className="sr-only">{index}. </span>}
            {title}
          </h2>
          {lead && <p className="card-lead">{lead}</p>}
        </div>
      </header>
      {children}
    </section>
  );
}
