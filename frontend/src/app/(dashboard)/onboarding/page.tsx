import OrganizationSetupForm from "@/components/organization/OrganizationSetupForm";

export const metadata = { title: "Create organisation — HireGraph" };

export default function OnboardingPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-zinc-900">
        Create your organisation
      </h1>
      <p className="mt-1 text-sm text-zinc-500">
        Your organisation is the workspace for your entire hiring team.
      </p>
      <div className="mt-8 max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <OrganizationSetupForm />
      </div>
    </div>
  );
}
