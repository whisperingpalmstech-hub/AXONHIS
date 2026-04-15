"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, ArrowLeft, Mail, Lock, Check, AlertTriangle, Loader2 } from "lucide-react";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [step, setStep] = useState<"email" | "reset">("email");
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [resetToken, setResetToken] = useState("");

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

  // Step 1: Check if email exists in the database
  const handleCheckEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${API}/api/v1/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");

      if (data.reset_token) {
        // Email found in DB — save token and move to password reset step
        setResetToken(data.reset_token);
        setStep("reset");
        setSuccess("Email verified! Please enter your new password.");
      } else {
        setError("This email is not registered in the system. Please check and try again.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to verify email");
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Reset password
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    // Validations
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match. Please re-enter.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: resetToken, new_password: newPassword }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Reset failed");
      setSuccess("Password changed successfully! Redirecting to login...");
      setTimeout(() => router.push("/login"), 2000);
    } catch (err: any) {
      setError(err.message || "Failed to reset password");
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
          <p className="text-[var(--text-secondary)] text-sm">Hospital Information System</p>
        </div>

        <div className="card">
          <div className="card-body">
            <h2 className="text-xl font-semibold text-center mb-2">
              {step === "email" ? "Forgot Password" : "Set New Password"}
            </h2>
            <p className="text-center text-sm text-[var(--text-secondary)] mb-6">
              {step === "email"
                ? "Enter your registered email to verify your account"
                : `Resetting password for ${email}`}
            </p>

            {/* Error Alert */}
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                <AlertTriangle size={16} className="shrink-0" /> {error}
              </div>
            )}

            {/* Success Alert */}
            {success && (
              <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm flex items-center gap-2">
                <Check size={16} className="shrink-0" /> {success}
              </div>
            )}

            {/* ── STEP 1: Email Verification ── */}
            {step === "email" && (
              <form onSubmit={handleCheckEmail} className="space-y-5">
                <div>
                  <label className="input-label" htmlFor="reset-email">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 text-gray-400" size={18} />
                    <input
                      id="reset-email"
                      type="email"
                      className="input-field pl-10"
                      placeholder="Enter your registered email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      autoFocus
                    />
                  </div>
                </div>

                <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                  {loading ? (
                    <><Loader2 size={16} className="animate-spin" /> Checking...</>
                  ) : (
                    "Verify Email"
                  )}
                </button>
              </form>
            )}

            {/* ── STEP 2: New Password ── */}
            {step === "reset" && (
              <form onSubmit={handleResetPassword} className="space-y-5">
                {/* New Password */}
                <div>
                  <label className="input-label" htmlFor="new-password">New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
                    <input
                      id="new-password"
                      type={showNewPassword ? "text" : "password"}
                      className="input-field pl-10 pr-10"
                      placeholder="Enter new password (min 6 chars)"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      minLength={6}
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700 transition-colors"
                      tabIndex={-1}
                      title={showNewPassword ? "Hide password" : "Show password"}
                    >
                      {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="input-label" htmlFor="confirm-password">Confirm New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
                    <input
                      id="confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      className="input-field pl-10 pr-10"
                      placeholder="Re-enter new password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      minLength={6}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700 transition-colors"
                      tabIndex={-1}
                      title={showConfirmPassword ? "Hide password" : "Show password"}
                    >
                      {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {/* Password match indicator */}
                {confirmPassword.length > 0 && (
                  <div className={`text-xs flex items-center gap-1 ${newPassword === confirmPassword ? "text-green-600" : "text-red-500"}`}>
                    {newPassword === confirmPassword ? (
                      <><Check size={14} /> Passwords match</>
                    ) : (
                      <><AlertTriangle size={14} /> Passwords do not match</>
                    )}
                  </div>
                )}

                <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                  {loading ? (
                    <><Loader2 size={16} className="animate-spin" /> Resetting...</>
                  ) : (
                    "Change Password"
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => { setStep("email"); setError(""); setSuccess(""); }}
                  className="w-full text-center text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                >
                  Use a different email
                </button>
              </form>
            )}

            {/* Back to Login */}
            <div className="mt-6 pt-4 border-t border-[var(--border)] text-center">
              <button
                type="button"
                onClick={() => router.push("/login")}
                className="text-sm text-[var(--accent-primary)] hover:underline font-medium flex items-center gap-2 justify-center mx-auto"
              >
                <ArrowLeft size={16} /> Back to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
