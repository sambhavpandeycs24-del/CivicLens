"use client";

import Link from "next/link";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const form = new FormData(event.currentTarget);
    try {
      if (mode === "register") {
        const response = await fetch(`${API}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: form.get("full_name"),
            email: form.get("email"),
            password: form.get("password"),
          }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail ?? "Registration failed");
        setMessage("Account created. You can now sign in.");
        setMode("login");
        return;
      }
      const body = new URLSearchParams();
      body.set("username", String(form.get("email") ?? ""));
      body.set("password", String(form.get("password") ?? ""));
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Sign in failed");
      window.localStorage.setItem("civiclens_access_token", data.access_token);
      setMessage("Signed in successfully.");
      window.location.assign("/report");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-md px-6 py-16">
      <Link href="/" className="text-sm font-semibold text-[#176b4b]">← CivicLens AI</Link>
      <h1 className="mt-8 text-3xl font-bold">{mode === "login" ? "Citizen sign in" : "Create citizen account"}</h1>
      <form onSubmit={submit} className="mt-7 grid gap-4 rounded-2xl border bg-white p-6">
        {mode === "register" && (
          <label className="grid gap-2 text-sm font-semibold">Full name
            <input name="full_name" required minLength={2} className="rounded border p-3" />
          </label>
        )}
        <label className="grid gap-2 text-sm font-semibold">Email
          <input name="email" type="email" required className="rounded border p-3" />
        </label>
        <label className="grid gap-2 text-sm font-semibold">Password
          <input name="password" type="password" required minLength={10} className="rounded border p-3" />
        </label>
        <button disabled={busy} className="rounded-full bg-[#176b4b] px-5 py-3 font-semibold text-white">
          {busy ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
        </button>
        <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")} className="text-sm font-semibold text-[#176b4b]">
          {mode === "login" ? "Create a citizen account" : "Already have an account? Sign in"}
        </button>
        {message && <p role="status" className="rounded bg-[#edf5ef] p-3 text-sm">{message}</p>}
      </form>
    </main>
  );
}
