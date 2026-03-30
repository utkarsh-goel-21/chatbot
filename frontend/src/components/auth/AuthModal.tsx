import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { X } from "lucide-react";
import DiamondIcon from "@/components/chat/DiamondIcon";

interface AuthModalProps {
  onClose: () => void;
  defaultMode?: "login" | "signup";
}

const AuthModal = ({ onClose, defaultMode = "login" }: AuthModalProps) => {
  const [mode, setMode] = useState<"login" | "signup">(defaultMode);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin,
      },
    });
    if (error) setError(error.message);
    setLoading(false);
  };

  const handleEmailAuth = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (!email || !password || (mode === "signup" && !name)) {
      setError("Please fill in all fields.");
      setLoading(false);
      return;
    }

    if (mode === "signup") {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: name,
          },
        },
      });
      if (error) setError(error.message);
      else setSuccess("Check your email for a confirmation link!");
    } else {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) setError(error.message);
      else onClose();
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-qm-surface border border-border rounded-2xl w-full max-w-[400px] p-6 relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-qm-text-muted hover:text-qm-text transition-colors"
        >
          <X size={18} />
        </button>

        {/* Logo */}
        <div className="flex items-center gap-2 mb-6">
          <DiamondIcon size={24} className="text-qm-accent" />
          <span className="text-lg font-bold text-qm-text">BizBot</span>
        </div>

        {/* Title */}
        <h2 className="text-xl font-bold text-qm-text mb-1">
          {mode === "login" ? "Welcome back" : "Create an account"}
        </h2>
        <p className="text-sm text-qm-text-sec mb-6">
          {mode === "login"
            ? "Sign in to access your data and conversations."
            : "Sign up to upload your own data and save conversations."}
        </p>

        {/* Google button */}
        <button
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full flex items-center justify-center gap-3 border border-border rounded-xl px-4 py-2.5 text-sm text-qm-text hover:bg-qm-elevated transition-colors mb-4 disabled:opacity-50"
        >
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path
              fill="#4285F4"
              d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"
            />
            <path
              fill="#34A853"
              d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2.04a4.8 4.8 0 0 1-7.18-2.54H1.83v2.07A8 8 0 0 0 8.98 17z"
            />
            <path
              fill="#FBBC05"
              d="M4.5 10.48A4.8 4.8 0 0 1 4.5 7.5V5.43H1.83a8 8 0 0 0 0 7.14z"
            />
            <path
              fill="#EA4335"
              d="M8.98 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.59A8 8 0 0 0 1.83 5.43L4.5 7.5a4.77 4.77 0 0 1 4.48-3.92z"
            />
          </svg>
          Continue with Google
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 border-t border-border" />
          <span className="text-xs text-qm-text-muted">or</span>
          <div className="flex-1 border-t border-border" />
        </div>

        {/* Name input (Signup only) */}
        {mode === "signup" && (
          <input
            type="text"
            placeholder="First Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-qm-elevated border border-border rounded-xl px-4 py-2.5 text-sm text-qm-text placeholder:text-qm-text-muted outline-none focus:border-qm-accent transition-colors mb-3"
          />
        )}

        {/* Email input */}
        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full bg-qm-elevated border border-border rounded-xl px-4 py-2.5 text-sm text-qm-text placeholder:text-qm-text-muted outline-none focus:border-qm-accent transition-colors mb-3"
        />

        {/* Password input */}
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleEmailAuth()}
          className="w-full bg-qm-elevated border border-border rounded-xl px-4 py-2.5 text-sm text-qm-text placeholder:text-qm-text-muted outline-none focus:border-qm-accent transition-colors mb-4"
        />

        {/* Error/Success messages */}
        {error && <p className="text-sm text-red-400 mb-3">{error}</p>}
        {success && <p className="text-sm text-qm-accent mb-3">{success}</p>}

        {/* Submit button */}
        <button
          onClick={handleEmailAuth}
          disabled={loading}
          className="w-full bg-qm-accent text-qm-base rounded-xl px-4 py-2.5 text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 mb-4"
        >
          {loading ? "Please wait..." : mode === "login" ? "Log in" : "Sign up"}
        </button>

        {/* Toggle mode */}
        <p className="text-center text-sm text-qm-text-sec">
          {mode === "login"
            ? "Don't have an account? "
            : "Already have an account? "}
          <button
            onClick={() => {
              setMode(mode === "login" ? "signup" : "login");
              setError(null);
              setSuccess(null);
            }}
            className="text-qm-accent hover:opacity-80 font-medium"
          >
            {mode === "login" ? "Sign up" : "Log in"}
          </button>
        </p>
      </div>
    </div>
  );
};

export default AuthModal;
