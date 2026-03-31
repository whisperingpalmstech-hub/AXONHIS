"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }
      );
      const data = await res.json();

      if (!res.ok) {
        if (Array.isArray(data.detail)) {
          setError(data.detail.map((err: any) => err.msg).join(", "));
        } else {
          setError(data.detail || "Login failed");
        }
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);

      // Fetch full user profile (with roles) and store for sidebar role-based rendering
      try {
        const meRes = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/auth/me`,
          { headers: { Authorization: `Bearer ${data.access_token}` } }
        );
        if (meRes.ok) {
          const profile = await meRes.json();
          // Determine primary role from the roles array
          const roleNames = (profile.roles || []).map((r: any) => (r.name || "").toLowerCase());
          let primaryRole = "admin"; // fallback
          const rolePriority = ["admin", "director", "doctor", "nurse", "pharmacist", "lab_technician", "front_desk"];
          for (const rp of rolePriority) {
            if (roleNames.includes(rp)) { primaryRole = rp; break; }
          }
          localStorage.setItem("user", JSON.stringify({
            ...profile,
            role: primaryRole,
            roleNames: roleNames,
          }));
        }
      } catch { /* profile fetch failed, sidebar will default to admin */ }

      router.push("/dashboard");
    } catch (err) {
      setError("Connection error. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
      <div className="w-full max-w-md px-4">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-[var(--accent-primary)] rounded-xl flex items-center justify-center">
              <span className="text-white text-2xl font-bold">A</span>
            </div>
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">
              AXON<span className="text-[var(--accent-primary)]">HIS</span>
            </h1>
          </div>
          <p className="text-[var(--text-secondary)] text-sm">
            Hospital Information System
          </p>
        </div>

        {/* Login Card */}
        <div className="card">
          <div className="card-body">
            <h2 className="text-xl font-semibold text-center mb-6">Sign In</h2>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-[var(--error-light)] text-[var(--error)] text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="input-label" htmlFor="email">Email Address</label>
                <input
                  id="email"
                  type="email"
                  className="input-field"
                  placeholder="doctor@hospital.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <div>
                <label className="input-label" htmlFor="password">Password</label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    className="input-field pr-10"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn-primary w-full"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  "Sign In"
                )}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-[var(--border)] text-center space-y-4">
              <p className="text-xs text-[var(--text-secondary)]">
                Default: admin@axonhis.local / Admin@123
              </p>
              <button type="button" onClick={() => router.push("/register-organization")} className="w-full py-2.5 bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 rounded-lg text-sm hover:bg-emerald-100 transition-colors">
                New Healthcare Provider? Provision Workspace
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-[var(--text-secondary)] mt-8">
          © 2026 Whispering Palms Tech Hub
        </p>
      </div>
    </div>
  );
}
