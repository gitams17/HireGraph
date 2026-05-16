import LoginForm from "@/components/auth/LoginForm";

export const metadata = { title: "Sign in — HireGraph" };

export default function LoginPage() {
  return (
    <>
      <h2 className="mb-6 text-xl font-semibold text-zinc-900">Sign in</h2>
      <LoginForm />
    </>
  );
}
