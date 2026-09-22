export function Banner({ kind, children }: { kind: "info" | "error"; children: React.ReactNode }) {
  return (
    <div className={`banner banner-${kind}`} role={kind === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}
