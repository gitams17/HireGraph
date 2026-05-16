import { redirect } from "next/navigation";

/**
 * Root page — immediately redirect to the dashboard.
 * Middleware handles the login redirect if the user is unauthenticated.
 */
export default function RootPage() {
  redirect("/dashboard");
}
