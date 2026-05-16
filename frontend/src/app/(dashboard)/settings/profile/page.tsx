import UserProfile from "@/components/settings/UserProfile";

export const metadata = { title: "Profile — HireGraph" };

export default function ProfileSettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-zinc-900">Profile</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Update your personal information.
      </p>
      <div className="mt-6 max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <UserProfile />
      </div>
    </div>
  );
}
