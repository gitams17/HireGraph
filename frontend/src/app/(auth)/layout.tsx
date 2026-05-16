/**
 * Auth route group layout.
 * Renders a centred card — no sidebar or nav.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 items-center justify-center min-h-screen bg-zinc-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
            HireGraph
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            AI-powered hiring orchestration
          </p>
        </div>
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
