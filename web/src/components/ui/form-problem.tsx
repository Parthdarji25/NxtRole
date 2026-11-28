/** Why a form could not be sent. Read out at once by screen readers. */
export function FormProblem({ children }: { children: string | null }) {
  if (!children) return null;
  return (
    <p role="alert" className="rounded-[10px] bg-red-soft px-3.5 py-2.5 text-sm text-red-ink">
      {children}
    </p>
  );
}
