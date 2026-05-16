import RegisterForm from "@/components/auth/RegisterForm";

export const metadata = { title: "Create account — HireGraph" };

export default function RegisterPage() {
  return (
    <>
      <h2 className="mb-6 text-xl font-semibold text-zinc-900">Create account</h2>
      <RegisterForm />
    </>
  );
}
