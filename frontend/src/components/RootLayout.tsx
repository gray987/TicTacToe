import { Outlet } from "react-router";

export function RootLayout() {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <header className="border-b border-slate-300 px-6 py-3">
        <p className="text-lg font-semibold">Ultimate Tic-Tac-Toe</p>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
